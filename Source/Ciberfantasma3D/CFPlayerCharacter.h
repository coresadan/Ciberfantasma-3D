#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CFPlayerCharacter.generated.h"

class ACFPulseProjectile;
class UCameraComponent;
class USpringArmComponent;
class UAnimSequence;
class UCFHeroAnimInstance;
class UPointLightComponent;
class UStaticMeshComponent;
class UNiagaraSystem;

UCLASS()
class CIBERFANTASMA3D_API ACFPlayerCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ACFPlayerCharacter();

    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual float TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent,
        AController* EventInstigator, AActor* DamageCauser) override;

    UFUNCTION(BlueprintPure, Category = "Ciberfantasma|Combat")
    bool IsShieldActive() const { return ShieldRemaining > 0.0f; }

    UFUNCTION(BlueprintCallable, Category = "Ciberfantasma|Combat")
    bool AbsorbProjectile(const FVector& ImpactLocation);

    void SetCheckpoint(const FVector& NewCheckpoint) { CheckpointLocation = NewCheckpoint; }
    int32 GetCurrentHealth() const { return CurrentHealth; }
    int32 GetMaxHealth() const { return MaxHealth; }
    float GetShieldReadyFraction() const;

protected:
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
    TObjectPtr<UCameraComponent> SideViewCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UStaticMeshComponent> ShieldVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UStaticMeshComponent> ShieldInnerVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UStaticMeshComponent> ShieldScanLine;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UStaticMeshComponent> ShieldFrameTop;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UStaticMeshComponent> ShieldFrameBottom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UStaticMeshComponent> ShieldFrameLeft;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UStaticMeshComponent> ShieldFrameRight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UPointLightComponent> ShieldLight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UPointLightComponent> MuzzleLight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ciberfantasma|Presentation")
    TObjectPtr<UStaticMeshComponent> MuzzleFlashVisual;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|VFX")
    TObjectPtr<UNiagaraSystem> ShieldAbsorbSystem;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Combat")
    TSubclassOf<ACFPulseProjectile> ProjectileClass;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> IdleAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> RunStartAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> RunAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> RunStopAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> JumpStartAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> JumpRiseAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> JumpFallAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> LandAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> CrouchAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> CrouchWalkAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> FireAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> FireBackAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> ShieldAnimation;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Animation")
    TObjectPtr<UAnimSequence> HitAnimation;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Combat", meta = (ClampMin = "0.05"))
    float FireCooldown = 0.22f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Combat", meta = (ClampMin = "0.05"))
    float ShieldDuration = 1.05f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Combat", meta = (ClampMin = "0.05"))
    float ShieldCooldown = 2.65f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health", meta = (ClampMin = "1"))
    int32 MaxHealth = 3;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Health")
    int32 CurrentHealth = 3;

    UFUNCTION(BlueprintImplementableEvent, Category = "Ciberfantasma|Presentation")
    void OnShieldVisualChanged(bool bActive);

    UFUNCTION(BlueprintImplementableEvent, Category = "Ciberfantasma|Presentation")
    void OnPulseFired();

    UFUNCTION(BlueprintImplementableEvent, Category = "Ciberfantasma|Presentation")
    void OnHealthChanged(int32 Current, int32 Maximum);

private:
    enum class EGroundLocomotionPhase : uint8
    {
        Idle,
        Starting,
        Running,
        Stopping
    };

    void MoveRight(float Value);
    void StartJump();
    void StopJump();
    void StartCrouch();
    void StopCrouch();
    void FirePulse();
    void FireLeft();
    void FireRight();
    void FireInDirection(float Direction);
    void ActivateShield();
    void ResetAtCheckpoint();
    void TogglePause();
    void RestartLevel();
    void RestartCampaign();
    void UpdateCharacterPresentation(float DeltaSeconds);
    void SetBaseAnimation(UAnimSequence* Animation, bool bLooping, float PlayRate = 1.0f,
        float BlendDuration = 0.14f);
    void TriggerCharacterAnimation(UAnimSequence* Animation, float LockDuration, float PlayRate = 1.0f);
    void TriggerAdditiveAnimation(UAnimSequence* Animation, float Duration, float PlayRate = 1.0f);
    void UpdateAnimationGraph(float DeltaSeconds);
    void UpdateFootIK(float DeltaSeconds);
    void UpdateAutomatedAnimationTest(float DeltaSeconds);
    void UpdateAutomatedEnemyTest(float DeltaSeconds);
    void UpdateAutomatedCrouchWalkTest(float DeltaSeconds);
    void UpdateAutomatedReverseFireTest(float DeltaSeconds);
    void UpdateAutomatedLocomotionTransitionTest(float DeltaSeconds);
    void UpdateAutomatedFootIKTest(float DeltaSeconds);
    bool SampleFootGround(FName FootBone, FVector& OutOffset, FQuat& OutRotation) const;
    UCFHeroAnimInstance* GetHeroAnimInstance() const;
    void SetShieldPresentation(bool bActive);
    bool CanAct() const;

    float FacingDirection = 1.0f;
    float ActiveFireDirection = 1.0f;
    float FireCooldownRemaining = 0.0f;
    float ShieldRemaining = 0.0f;
    float ShieldCooldownRemaining = 0.0f;
    float DamageInvulnerabilityRemaining = 0.0f;
    float AnimationLockRemaining = 0.0f;
    float MuzzleFlashRemaining = 0.0f;
    float CameraLandingOffset = 0.0f;
    float MovementInputValue = 0.0f;
    float GroundLocomotionPhaseTime = 0.0f;
    EGroundLocomotionPhase GroundLocomotionPhase = EGroundLocomotionPhase::Idle;
    bool bWasGrounded = true;
    bool bLastShotContralateral = false;
    FVector CheckpointLocation = FVector::ZeroVector;
    TObjectPtr<UAnimSequence> CurrentBaseAnimation;
    TObjectPtr<UAnimSequence> PreviousBaseAnimation;
    TObjectPtr<UAnimSequence> AdditiveAnimation;
    float CurrentBaseTime = 0.0f;
    float PreviousBaseTime = 0.0f;
    float CurrentBasePlayRate = 1.0f;
    float PreviousBasePlayRate = 1.0f;
    float BaseBlendElapsed = 0.0f;
    float BaseBlendDuration = 0.14f;
    float AdditiveTime = 0.0f;
    float AdditiveDuration = 0.0f;
    float AdditivePlayRate = 1.0f;
    int32 CurrentBaseTrack = 0;
    bool bCurrentBaseLooping = true;
    bool bPreviousBaseLooping = true;
    bool bAutomatedAnimationTest = false;
    bool bAutomatedDirectionTestPassed = true;
    float AutomatedTestTime = 0.0f;
    int32 AutomatedTestStage = 0;
    bool bAutomatedEnemyTest = false;
    float AutomatedEnemyTestTime = 0.0f;
    int32 AutomatedEnemyTestStage = 0;
    bool bAutomatedCrouchWalkTest = false;
    float AutomatedCrouchWalkTestTime = 0.0f;
    int32 AutomatedCrouchWalkTestStage = 0;
    float AutomatedCrouchWalkSampleTime = 0.0f;
    bool bAutomatedReverseFireTest = false;
    float AutomatedReverseFireTestTime = 0.0f;
    int32 AutomatedReverseFireTestStage = 0;
    bool bAutomatedLocomotionTransitionTest = false;
    float AutomatedLocomotionTransitionTestTime = 0.0f;
    int32 AutomatedLocomotionTransitionTestStage = 0;
    FVector LeftFootIKOffset = FVector::ZeroVector;
    FVector RightFootIKOffset = FVector::ZeroVector;
    FQuat LeftFootIKRotation = FQuat::Identity;
    FQuat RightFootIKRotation = FQuat::Identity;
    float PelvisIKOffset = 0.0f;
    float FootIKAlpha = 0.0f;
    bool bLeftFootHasGround = false;
    bool bRightFootHasGround = false;
    bool bAutomatedFootIKTest = false;
    float AutomatedFootIKTestTime = 0.0f;
};
