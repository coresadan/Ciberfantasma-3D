#include "CFPulseProjectile.h"

#include "CFPlayerCharacter.h"
#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "UObject/ConstructorHelpers.h"

ACFPulseProjectile::ACFPulseProjectile()
{
    PrimaryActorTick.bCanEverTick = false;
    InitialLifeSpan = 1.2f;

    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
    Collision->InitSphereRadius(12.0f);
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Collision->SetCollisionObjectType(ECC_WorldDynamic);
    Collision->SetCollisionResponseToAllChannels(ECR_Block);
    Collision->SetNotifyRigidBodyCollision(true);
    RootComponent = Collision;

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetRelativeScale3D(FVector(0.28f, 0.09f, 0.09f));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (SphereMesh.Succeeded())
    {
        Visual->SetStaticMesh(SphereMesh.Object);
    }
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> PulseMaterial(
        TEXT("/Game/Art/Materials/M_CF_Pulse_V6.M_CF_Pulse_V6"));
    if (PulseMaterial.Succeeded())
    {
        Visual->SetMaterial(0, PulseMaterial.Object);
    }

    TrailVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TrailVisual"));
    TrailVisual->SetupAttachment(Collision);
    TrailVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    TrailVisual->SetRelativeLocation(FVector(-24.0f, 0.0f, 0.0f));
    TrailVisual->SetRelativeScale3D(FVector(0.42f, 0.045f, 0.045f));
    TrailVisual->CastShadow = false;
    if (SphereMesh.Succeeded()) TrailVisual->SetStaticMesh(SphereMesh.Object);
    if (PulseMaterial.Succeeded()) TrailVisual->SetMaterial(0, PulseMaterial.Object);

    PulseLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("PulseLight"));
    PulseLight->SetupAttachment(Collision);
    PulseLight->SetLightColor(FLinearColor(0.05f, 1.0f, 0.25f));
    PulseLight->Intensity = 820.0f;
    PulseLight->AttenuationRadius = 190.0f;

    Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
    Movement->UpdatedComponent = Collision;
    Movement->InitialSpeed = 1450.0f;
    Movement->MaxSpeed = 1450.0f;
    Movement->ProjectileGravityScale = 0.0f;
    Movement->bRotationFollowsVelocity = true;

    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> ImpactAsset(
        TEXT("/Game/Art/VFX/NS_PulseImpact_Runtime.NS_PulseImpact_Runtime"));
    ImpactSystem = ImpactAsset.Object;

    Collision->OnComponentHit.AddDynamic(this, &ACFPulseProjectile::HandleHit);
}

void ACFPulseProjectile::BeginPlay()
{
    Super::BeginPlay();
    Collision->IgnoreActorWhenMoving(GetOwner(), true);
}

void ACFPulseProjectile::HandleHit(UPrimitiveComponent* HitComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit)
{
    if (OtherActor == nullptr || OtherActor == GetOwner())
    {
        return;
    }

    if (ACFPlayerCharacter* Player = Cast<ACFPlayerCharacter>(OtherActor))
    {
        if (Player->AbsorbProjectile(Hit.ImpactPoint))
        {
            Destroy();
            return;
        }
    }

    if (ImpactSystem)
    {
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ImpactSystem, Hit.ImpactPoint,
            Hit.ImpactNormal.Rotation(), FVector(0.18f));
    }

    UGameplayStatics::ApplyPointDamage(OtherActor, Damage, GetActorForwardVector(), Hit,
        GetInstigatorController(), this, UDamageType::StaticClass());
    Destroy();
}
