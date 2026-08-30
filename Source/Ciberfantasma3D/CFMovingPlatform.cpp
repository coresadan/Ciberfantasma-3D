#include "CFMovingPlatform.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
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
        Collision->SetCollisionEnabled(bActive ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
        Visual->SetVisibility(bActive);
        return;
    }
    FVector Offset = FVector::ZeroVector;
    const float Travel = FMath::Sin(Time * MovementSpeed + PhaseOffset) * MovementRange;
    if (bHorizontal) Offset.X = Travel;
    else Offset.Z = Travel;
    SetActorLocation(Origin + Offset);
}
