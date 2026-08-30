#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CFPatrolEnemy.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UPrimitiveComponent;
class UPointLightComponent;
class ACFEnemyProjectile;
class UNiagaraSystem;

UCLASS()
class CIBERFANTASMA3D_API ACFPatrolEnemy : public ACharacter
{
    GENERATED_BODY()

public:
    ACFPatrolEnemy();
    virtual void Tick(float DeltaSeconds) override;
    virtual float TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent,
        AController* EventInstigator, AActor* DamageCauser) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Enemy")
    int32 EnemyKind = 0;

protected:
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Art")
    TObjectPtr<UStaticMeshComponent> DevelopmentVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Art")
    TObjectPtr<UPointLightComponent> EnemyGlow;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Art")
    TObjectPtr<UStaticMeshComponent> ProfileCore;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Art")
    TObjectPtr<UStaticMeshComponent> ProfileFinLeft;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Art")
    TObjectPtr<UStaticMeshComponent> ProfileFinRight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Art")
    TObjectPtr<UStaticMeshComponent> ProfileCannon;

    // Hard references keep every runtime-selected enemy mesh discoverable by the cooker.
    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Art")
    TArray<TObjectPtr<UStaticMesh>> EnemyMeshes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Patrol")
    float PatrolDistance = 320.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Patrol")
    float PatrolSpeed = 140.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float ContactDamage = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float MaxHealth = 3.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    TSubclassOf<ACFEnemyProjectile> EnemyProjectileClass;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|VFX")
    TObjectPtr<UNiagaraSystem> DeathSystem;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|VFX")
    TObjectPtr<UNiagaraSystem> BossExplosionSystem;

private:
    UFUNCTION()
    void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

    float CurrentHealth = 3.0f;
    float PatrolDirection = 1.0f;
    float OriginX = 0.0f;
    float OriginZ = 0.0f;
    float ShotCooldown = 1.0f;
    float DashCooldown = 0.8f;
    float AttackWindupRemaining = 0.0f;
    float AttackRecoilRemaining = 0.0f;
    float HitReactionRemaining = 0.0f;
    float ProfileScale = 1.0f;
    int32 PendingShotCount = 0;
    float PendingShotSpread = 0.0f;
    bool bPendingHeavyShot = false;
    bool bAttackQueued = false;
    bool bRegistered = false;

    bool IsBoss() const;
    bool IsFlying() const;
    void ApplyProfile();
    void QueueAttack(int32 Count, float Spread, bool bHeavy);
    void UpdatePresentation(float DeltaSeconds);
    void FireAtPlayer(int32 Count = 1, float Spread = 0.0f, bool bHeavy = false);
};
