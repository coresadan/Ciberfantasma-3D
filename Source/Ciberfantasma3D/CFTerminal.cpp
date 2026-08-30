#include "CFTerminal.h"

#include "CFGameState.h"
#include "CFPlayerCharacter.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"

ACFTerminal::ACFTerminal()
{
    Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
    Trigger->InitBoxExtent(FVector(55.0f, 90.0f, 75.0f));
    Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
    Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    Trigger->OnComponentBeginOverlap.AddDynamic(this, &ACFTerminal::HandleOverlap);
    RootComponent = Trigger;

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Trigger);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetRelativeScale3D(FVector(0.7f, 0.8f, 1.25f));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) Visual->SetStaticMesh(Cube.Object);

    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Trigger);
    Glow->SetLightColor(FLinearColor(0.02f, 0.65f, 1.0f));
    Glow->Intensity = 900.0f;
    Glow->AttenuationRadius = 300.0f;
}

void ACFTerminal::HandleOverlap(UPrimitiveComponent*, AActor* OtherActor,
    UPrimitiveComponent*, int32, bool, const FHitResult&)
{
    if (bHacked) return;
    if (ACFPlayerCharacter* Player = Cast<ACFPlayerCharacter>(OtherActor))
    {
        bHacked = true;
        Player->SetCheckpoint(GetActorLocation() + FVector(-110.0f, 0.0f, 80.0f));
        if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->HackTerminal();
        Glow->SetLightColor(FLinearColor(0.05f, 1.0f, 0.2f));
        Glow->SetIntensity(2200.0f);
    }
}
