#include "CFMovingPlatform.h"

#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ACFMovingPlatform::ACFMovingPlatform()
{
    PrimaryActorTick.bCanEverTick = true;
    Collision = CreateDefaultSubobject<UBoxComponent>(TEXT("Collision"));
    Collision->InitBoxExtent(FVector(50.0f));
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Collision->SetCollisionResponseToAllChannels(ECR_Block);
    Collision->SetMobility(EComponentMobility::Movable);
    RootComponent = Collision;

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) Visual->SetStaticMesh(Cube.Object);

    Accent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Accent"));
    Accent->SetupAttachment(Collision);
    Accent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Accent->CastShadow = false;
    Accent->SetRelativeLocation(FVector(0.0f, -51.0f, 37.0f));
    Accent->SetRelativeScale3D(FVector(0.82f, 0.035f, 0.12f));
    if (Cube.Succeeded()) Accent->SetStaticMesh(Cube.Object);

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> PulseMaterial(
        TEXT("/Game/Art/Materials/M_CF_Pulse_V9.M_CF_Pulse_V9"));
    if (PulseMaterial.Succeeded()) Accent->SetMaterial(0, PulseMaterial.Object);

    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Collision);
    Glow->SetLightColor(FLinearColor(0.05f, 0.82f, 1.0f));
    Glow->Intensity = 420.0f;
    Glow->AttenuationRadius = 280.0f;
    Glow->CastShadows = false;
}

void ACFMovingPlatform::BeginPlay()
{
    Super::BeginPlay();
    Origin = GetActorLocation();
}

void ACFMovingPlatform::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float Time = GetWorld()->GetTimeSeconds();
    if (bPhasePlatform)
    {
        const float Cycle = FMath::Fmod(Time + PhaseOffset, 3.2f);
        const bool bActive = Cycle < 2.18f;
        const bool bWarning = Cycle > 1.72f && bActive;
        const bool bTelegraphVisible = !bWarning || FMath::Sin(Time * 34.0f) > -0.25f;
        Collision->SetCollisionEnabled(bActive ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
        Visual->SetVisibility(bActive && bTelegraphVisible);
        Accent->SetVisibility(bActive);
        Accent->SetRelativeScale3D(FVector(0.82f + 0.08f * FMath::Sin(Time * 8.0f), 0.035f, 0.12f));
        Glow->SetIntensity(bActive ? (bWarning ? 900.0f : 520.0f) : 90.0f);
        return;
    }
    FVector Offset = FVector::ZeroVector;
    const float Travel = FMath::Sin(Time * MovementSpeed + PhaseOffset) * MovementRange;
    if (bHorizontal) Offset.X = Travel;
    else Offset.Z = Travel;
    SetActorLocation(Origin + Offset);
    const float Pulse = 0.5f + 0.5f * FMath::Sin(Time * 7.0f + PhaseOffset);
    Accent->SetRelativeScale3D(FVector(0.76f + Pulse * 0.12f, 0.035f, 0.11f));
    Glow->SetIntensity(300.0f + Pulse * 320.0f);
}
