#include "CFHazard.h"

#include "CFPlayerCharacter.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

ACFHazard::ACFHazard()
{
    PrimaryActorTick.bCanEverTick = false;

    Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
    Trigger->InitBoxExtent(FVector(50.0f));
    Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
    Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    Trigger->OnComponentBeginOverlap.AddDynamic(this, &ACFHazard::HandleOverlap);
    RootComponent = Trigger;

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Trigger);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (CubeMesh.Succeeded())
    {
        Visual->SetStaticMesh(CubeMesh.Object);
    }

    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Trigger);
    Glow->SetLightColor(FLinearColor(1.0f, 0.01f, 0.08f));
    Glow->Intensity = 1200.0f;
    Glow->AttenuationRadius = 260.0f;
}

void ACFHazard::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (ACFPlayerCharacter* Player = Cast<ACFPlayerCharacter>(OtherActor))
    {
        UGameplayStatics::ApplyDamage(Player, 1.0f, nullptr, this, UDamageType::StaticClass());
    }
}
