#include "CFHazard.h"

#include "CFPlayerCharacter.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ACFHazard::ACFHazard()
{
    PrimaryActorTick.bCanEverTick = true;

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

    DetailA = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DetailA"));
    DetailA->SetupAttachment(Trigger);
    DetailA->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    DetailA->CastShadow = false;
    DetailB = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DetailB"));
    DetailB->SetupAttachment(Trigger);
    DetailB->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    DetailB->CastShadow = false;
    if (CubeMesh.Succeeded())
    {
        DetailA->SetStaticMesh(CubeMesh.Object);
        DetailB->SetStaticMesh(CubeMesh.Object);
    }

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> HazardMaterial(
        TEXT("/Game/Art/Materials/M_Enemy_Red_V8.M_Enemy_Red_V8"));
    if (HazardMaterial.Succeeded())
    {
        Visual->SetMaterial(0, HazardMaterial.Object);
        DetailA->SetMaterial(0, HazardMaterial.Object);
        DetailB->SetMaterial(0, HazardMaterial.Object);
    }

    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Trigger);
    Glow->SetLightColor(FLinearColor(1.0f, 0.01f, 0.08f));
    Glow->Intensity = 1200.0f;
    Glow->AttenuationRadius = 260.0f;
    Glow->CastShadows = false;
}

void ACFHazard::BeginPlay()
{
    Super::BeginPlay();
    if (HazardStyle == TEXT("laserFence"))
    {
        Visual->SetRelativeScale3D(FVector(0.90f, 0.24f, 0.055f));
        DetailA->SetRelativeLocation(FVector(-43.0f, 0.0f, 0.0f));
        DetailB->SetRelativeLocation(FVector(43.0f, 0.0f, 0.0f));
        DetailA->SetRelativeScale3D(FVector(0.055f, 0.34f, 1.0f));
        DetailB->SetRelativeScale3D(FVector(0.055f, 0.34f, 1.0f));
        Glow->SetLightColor(FLinearColor(1.0f, 0.01f, 0.04f));
    }
    else if (HazardStyle == TEXT("memory"))
    {
        Visual->SetRelativeScale3D(FVector(0.86f, 0.50f, 0.28f));
        DetailA->SetRelativeLocation(FVector(-25.0f, -28.0f, 24.0f));
        DetailB->SetRelativeLocation(FVector(25.0f, -28.0f, 24.0f));
        DetailA->SetRelativeScale3D(FVector(0.19f, 0.08f, 0.22f));
        DetailB->SetRelativeScale3D(FVector(0.19f, 0.08f, 0.22f));
        Glow->SetLightColor(FLinearColor(0.72f, 0.12f, 1.0f));
    }
    else if (HazardStyle == TEXT("shredder") || HazardStyle == TEXT("shredderPaper"))
    {
        Visual->SetRelativeScale3D(FVector(0.86f, 0.46f, 0.18f));
        DetailA->SetRelativeLocation(FVector(-24.0f, -30.0f, 24.0f));
        DetailB->SetRelativeLocation(FVector(24.0f, -30.0f, 24.0f));
        DetailA->SetRelativeScale3D(FVector(0.24f, 0.07f, 0.24f));
        DetailB->SetRelativeScale3D(FVector(0.24f, 0.07f, 0.24f));
        Glow->SetLightColor(FLinearColor(1.0f, 0.22f, 0.01f));
    }
    else
    {
        Visual->SetRelativeScale3D(FVector(0.84f, 0.48f, 0.26f));
        DetailA->SetRelativeLocation(FVector(-27.0f, -25.0f, 25.0f));
        DetailB->SetRelativeLocation(FVector(27.0f, -25.0f, 25.0f));
        DetailA->SetRelativeScale3D(FVector(0.16f, 0.10f, 0.30f));
        DetailB->SetRelativeScale3D(FVector(0.16f, 0.10f, 0.30f));
    }
}

void ACFHazard::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float Time = GetWorld()->GetTimeSeconds();
    const float Pulse = 0.5f + 0.5f * FMath::Sin(Time * 8.0f);
    Glow->SetIntensity(620.0f + Pulse * 980.0f);
    if (HazardStyle == TEXT("shredder") || HazardStyle == TEXT("shredderPaper"))
    {
        DetailA->AddLocalRotation(FRotator(0.0f, 0.0f, 280.0f * DeltaSeconds));
        DetailB->AddLocalRotation(FRotator(0.0f, 0.0f, -320.0f * DeltaSeconds));
    }
    else if (HazardStyle == TEXT("laserFence"))
    {
        Visual->SetVisibility(FMath::Sin(Time * 22.0f) > -0.78f);
    }
}

void ACFHazard::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (ACFPlayerCharacter* Player = Cast<ACFPlayerCharacter>(OtherActor))
    {
        UGameplayStatics::ApplyDamage(Player, 1.0f, nullptr, this, UDamageType::StaticClass());
    }
}
