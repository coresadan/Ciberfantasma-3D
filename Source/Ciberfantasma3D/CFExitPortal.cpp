#include "CFExitPortal.h"

#include "CFGameState.h"
#include "CFPlayerCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"

ACFExitPortal::ACFExitPortal()
{
    PrimaryActorTick.bCanEverTick = true;

    Trigger = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Trigger"));
    Trigger->InitCapsuleSize(70.0f, 135.0f);
    Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
    Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    Trigger->OnComponentBeginOverlap.AddDynamic(this, &ACFExitPortal::HandleOverlap);
    RootComponent = Trigger;

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Trigger);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetRelativeScale3D(FVector(0.8f, 0.8f, 1.5f));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (CylinderMesh.Succeeded())
    {
        Visual->SetStaticMesh(CylinderMesh.Object);
    }

    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Trigger);
    Glow->SetLightColor(FLinearColor(0.03f, 0.35f, 0.4f));
    Glow->Intensity = 700.0f;
    Glow->AttenuationRadius = 420.0f;
}

void ACFExitPortal::BeginPlay()
{
    Super::BeginPlay();
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>())
    {
        State->ConfigureLevel(LevelIndex, LevelName, LevelTitle);
    }
}

void ACFExitPortal::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bUnlocked)
    {
        return;
    }
    if (const ACFGameState* State = GetWorld()->GetGameState<ACFGameState>(); State && State->CanExit())
    {
        bUnlocked = true;
        Glow->SetLightColor(FLinearColor(0.04f, 1.0f, 0.22f));
        Glow->Intensity = 2600.0f;
        OnPortalUnlocked();
    }
}

void ACFExitPortal::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (bUnlocked && !bCompleted && OtherActor->IsA<ACFPlayerCharacter>())
    {
        bCompleted = true;
        OnLevelCompleted();
        if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->CompleteLevel();
    }
}
