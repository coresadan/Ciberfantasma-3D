#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CFPulseProjectile.generated.h"

class UProjectileMovementComponent;
class UPointLightComponent;
class USphereComponent;
class UStaticMeshComponent;
class UPrimitiveComponent;
class UNiagaraSystem;

UCLASS()
class CIBERFANTASMA3D_API ACFPulseProjectile : public AActor
{
    GENERATED_BODY()

public:
    ACFPulseProjectile();

protected:
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
    TObjectPtr<USphereComponent> Collision;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
    TObjectPtr<UProjectileMovementComponent> Movement;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
    TObjectPtr<UStaticMeshComponent> Visual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|VFX")
    TObjectPtr<UStaticMeshComponent> TrailVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
    TObjectPtr<UPointLightComponent> PulseLight;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile")
    float Damage = 1.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|VFX")
    TObjectPtr<UNiagaraSystem> ImpactSystem;

private:
    UFUNCTION()
    void HandleHit(UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComponent,
        FVector NormalImpulse, const FHitResult& Hit);
};
