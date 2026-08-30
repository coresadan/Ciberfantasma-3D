#include "CFEnemyProjectile.h"

#include "CFPlayerCharacter.h"
#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

ACFEnemyProjectile::ACFEnemyProjectile()
{
    InitialLifeSpan = 4.5f;
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
    Collision->InitSphereRadius(13.0f);
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Collision->SetCollisionResponseToAllChannels(ECR_Block);
    Collision->SetNotifyRigidBodyCollision(true);
    RootComponent = Collision;

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetRelativeScale3D(FVector(0.26f, 0.1f, 0.1f));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (Sphere.Succeeded()) Visual->SetStaticMesh(Sphere.Object);

    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Collision);
    Glow->SetLightColor(FLinearColor(1.0f, 0.02f, 0.18f));
    Glow->Intensity = 1600.0f;
    Glow->AttenuationRadius = 260.0f;

    Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
    Movement->UpdatedComponent = Collision;
    Movement->ProjectileGravityScale = 0.0f;
    Movement->bRotationFollowsVelocity = true;
    Collision->OnComponentHit.AddDynamic(this, &ACFEnemyProjectile::HandleHit);
}

void ACFEnemyProjectile::Launch(const FVector& Direction, float Speed, bool bInHeavy)
{
    bHeavy = bInHeavy;
    const float Scale = bHeavy ? 1.8f : 1.0f;
    Collision->SetSphereRadius(13.0f * Scale);
    Visual->SetRelativeScale3D(FVector(0.26f, 0.1f, 0.1f) * Scale);
    Glow->SetLightColor(bHeavy ? FLinearColor(1.0f, 0.01f, 0.03f) : FLinearColor(1.0f, 0.05f, 0.25f));
    Movement->Velocity = Direction.GetSafeNormal() * Speed;
    Movement->InitialSpeed = Speed;
    Movement->MaxSpeed = Speed;
}

void ACFEnemyProjectile::HandleHit(UPrimitiveComponent*, AActor* OtherActor,
    UPrimitiveComponent*, FVector, const FHitResult& Hit)
{
    if (!OtherActor || OtherActor == GetOwner()) return;
    if (ACFPlayerCharacter* Player = Cast<ACFPlayerCharacter>(OtherActor))
    {
        if (Player->AbsorbProjectile(Hit.ImpactPoint))
        {
            Destroy();
            return;
        }
        UGameplayStatics::ApplyDamage(Player, 1.0f, GetInstigatorController(), this, UDamageType::StaticClass());
    }
    Destroy();
}
