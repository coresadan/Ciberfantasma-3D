#include "CFShard.h"

#include "CFGameState.h"
#include "CFPlayerCharacter.h"
#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"

ACFShard::ACFShard()
{
    PrimaryActorTick.bCanEverTick = true;

    Trigger = CreateDefaultSubobject<USphereComponent>(TEXT("Trigger"));
    Trigger->InitSphereRadius(45.0f);
    Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
    Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    Trigger->OnComponentBeginOverlap.AddDynamic(this, &ACFShard::HandleOverlap);
    RootComponent = Trigger;

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Trigger);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetRelativeScale3D(FVector(0.28f, 0.28f, 0.5f));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (SphereMesh.Succeeded())
    {
        Visual->SetStaticMesh(SphereMesh.Object);
    }

    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Trigger);
    Glow->SetLightColor(FLinearColor(0.04f, 1.0f, 0.22f));
    Glow->Intensity = 1800.0f;
    Glow->AttenuationRadius = 300.0f;
}

void ACFShard::BeginPlay()
{
    Super::BeginPlay();
    InitialZ = GetActorLocation().Z;
    TimeOffset = FMath::FRandRange(0.0f, PI * 2.0f);
}

void ACFShard::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    AddActorLocalRotation(FRotator(0.0f, 90.0f * DeltaSeconds, 0.0f));
    FVector Location = GetActorLocation();
    Location.Z = InitialZ + FMath::Sin(GetWorld()->GetTimeSeconds() * 2.5f + TimeOffset) * 14.0f;
    SetActorLocation(Location);
}

void ACFShard::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (!OtherActor->IsA<ACFPlayerCharacter>())
    {
        return;
    }
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>())
    {
        State->CollectShard();
    }
    Destroy();
}
