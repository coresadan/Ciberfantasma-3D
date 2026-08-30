#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CFEnemyProjectile.generated.h"

class UPointLightComponent;
class UProjectileMovementComponent;
class USphereComponent;
class UStaticMeshComponent;

UCLASS()
class CIBERFANTASMA3D_API ACFEnemyProjectile : public AActor
{
    GENERATED_BODY()

public:
    ACFEnemyProjectile();
    void Launch(const FVector& Direction, float Speed, bool bInHeavy = false);

private:
    UFUNCTION()
    void HandleHit(UPrimitiveComponent* HitComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USphereComponent> Collision;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UPointLightComponent> Glow;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UProjectileMovementComponent> Movement;

    bool bHeavy = false;
};
