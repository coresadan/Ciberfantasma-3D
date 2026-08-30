#include "CFPlayerCharacter.h"

#include "CFGameInstance.h"
#include "CFGameState.h"
#include "CFPulseProjectile.h"
#include "CFPatrolEnemy.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "AnimSequencerInstance.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/PlatformMisc.h"
#include "UnrealClient.h"
#include "EngineUtils.h"

ACFPlayerCharacter::ACFPlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    GetCapsuleComponent()->InitCapsuleSize(42.0f, 92.0f);

    UCharacterMovementComponent* Movement = GetCharacterMovement();
    Movement->GravityScale = 1.0f;
    Movement->AirControl = 0.72f;
    Movement->JumpZVelocity = 700.0f;
    Movement->MaxWalkSpeed = 720.0f;
    Movement->GroundFriction = 9.0f;
    Movement->BrakingDecelerationWalking = 2200.0f;
    Movement->bOrientRotationToMovement = false;
    Movement->bConstrainToPlane = true;
    Movement->SetPlaneConstraintNormal(FVector(0.0f, 1.0f, 0.0f));
    Movement->bSnapToPlaneAtStart = true;
    Movement->GetNavAgentPropertiesRef().bCanCrouch = true;
    Movement->SetCrouchedHalfHeight(55.0f);

    JumpMaxCount = 2;
    JumpMaxHoldTime = 0.12f;
    bUseControllerRotationYaw = false;

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->SetUsingAbsoluteRotation(true);
    CameraBoom->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    CameraBoom->TargetArmLength = 1050.0f;
    CameraBoom->bDoCollisionTest = false;
    CameraBoom->bEnableCameraLag = true;
    CameraBoom->CameraLagSpeed = 8.0f;

    SideViewCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("SideViewCamera"));
    SideViewCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    SideViewCamera->bUsePawnControlRotation = false;
    SideViewCamera->FieldOfView = 36.0f;

    ShieldVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldVisual"));
    ShieldVisual->SetupAttachment(RootComponent);
    ShieldVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ShieldVisual->SetRelativeScale3D(FVector(1.18f, 0.86f, 1.82f));
    ShieldVisual->SetVisibility(false);
    ShieldVisual->CastShadow = false;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ShieldSphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (ShieldSphere.Succeeded())
    {
        ShieldVisual->SetStaticMesh(ShieldSphere.Object);
    }
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ShieldMaterial(
        TEXT("/Game/Art/Materials/M_CF_Shield_V6.M_CF_Shield_V6"));
    if (ShieldMaterial.Succeeded())
    {
        ShieldVisual->SetMaterial(0, ShieldMaterial.Object);
    }

    ShieldLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("ShieldLight"));
    ShieldLight->SetupAttachment(RootComponent);
    ShieldLight->SetLightColor(FLinearColor(0.0f, 1.0f, 0.08f));
    ShieldLight->SetAttenuationRadius(330.0f);
    ShieldLight->SetIntensity(0.0f);
    ShieldLight->CastShadows = false;

    MuzzleLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("MuzzleLight"));
    MuzzleLight->SetupAttachment(RootComponent);
    MuzzleLight->SetLightColor(FLinearColor(0.05f, 1.0f, 0.18f));
    MuzzleLight->SetAttenuationRadius(240.0f);
    MuzzleLight->SetIntensity(0.0f);
    MuzzleLight->CastShadows = false;

    MuzzleFlashVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MuzzleFlashVisual"));
    MuzzleFlashVisual->SetupAttachment(RootComponent);
    MuzzleFlashVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    MuzzleFlashVisual->SetVisibility(false);
    MuzzleFlashVisual->CastShadow = false;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> MuzzleCone(TEXT("/Engine/BasicShapes/Cone.Cone"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> PulseCoreMaterial(
        TEXT("/Game/Art/Materials/M_CF_Pulse_V6.M_CF_Pulse_V6"));
    if (MuzzleCone.Succeeded()) MuzzleFlashVisual->SetStaticMesh(MuzzleCone.Object);
    if (PulseCoreMaterial.Succeeded()) MuzzleFlashVisual->SetMaterial(0, PulseCoreMaterial.Object);

    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> MuzzleFlashAsset(
        TEXT("/Game/Art/VFX/NS_MuzzleFlash_Runtime.NS_MuzzleFlash_Runtime"));
    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> ShieldAbsorbAsset(
        TEXT("/Game/Art/VFX/NS_ShieldAbsorb_Runtime.NS_ShieldAbsorb_Runtime"));
    MuzzleFlashSystem = MuzzleFlashAsset.Object;
    ShieldAbsorbSystem = ShieldAbsorbAsset.Object;

    USkeletalMeshComponent* CharacterVisual = GetMesh();
    CharacterVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> CharacterMesh(
        TEXT("/Game/Art/Characters/SK_Ciberfantasma_Chibi_Pro.SK_Ciberfantasma_Chibi_Pro"));
    if (CharacterMesh.Succeeded())
    {
        CharacterVisual->SetSkeletalMeshAsset(CharacterMesh.Object);
        CharacterVisual->SetRelativeLocation(FVector(0.0f, 0.0f, -92.0f));
        CharacterVisual->SetRelativeRotation(FRotator::ZeroRotator);
        CharacterVisual->SetRelativeScale3D(FVector::OneVector);
        CharacterVisual->SetAnimationMode(EAnimationMode::AnimationBlueprint);
        CharacterVisual->SetAnimInstanceClass(UAnimSequencerInstance::StaticClass());
    }

    static ConstructorHelpers::FObjectFinder<UAnimSequence> IdleAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Idle.A_Ciberfantasma_Pro_Idle"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> RunAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Run.A_Ciberfantasma_Pro_Run"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpStartAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_JumpStart.A_Ciberfantasma_Pro_JumpStart"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpRiseAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_JumpRise.A_Ciberfantasma_Pro_JumpRise"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpFallAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_JumpFall.A_Ciberfantasma_Pro_JumpFall"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> LandAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Land.A_Ciberfantasma_Pro_Land"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> CrouchAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Crouch.A_Ciberfantasma_Pro_Crouch"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> FireAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Fire.A_Ciberfantasma_Pro_Fire"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> ShieldAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Shield.A_Ciberfantasma_Pro_Shield"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> HitAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Hit.A_Ciberfantasma_Pro_Hit"));
    IdleAnimation = IdleAsset.Object;
    RunAnimation = RunAsset.Object;
    JumpStartAnimation = JumpStartAsset.Object;
    JumpRiseAnimation = JumpRiseAsset.Object;
    JumpFallAnimation = JumpFallAsset.Object;
    LandAnimation = LandAsset.Object;
    CrouchAnimation = CrouchAsset.Object;
    FireAnimation = FireAsset.Object;
    ShieldAnimation = ShieldAsset.Object;
    HitAnimation = HitAsset.Object;

    ProjectileClass = ACFPulseProjectile::StaticClass();
}

void ACFPlayerCharacter::BeginPlay()
{
    Super::BeginPlay();
    SetActorRotation(FRotator::ZeroRotator);
    CurrentHealth = MaxHealth;
    CheckpointLocation = GetActorLocation();
    bWasGrounded = GetCharacterMovement()->IsMovingOnGround();
    bAutomatedAnimationTest = FParse::Param(FCommandLine::Get(), TEXT("CFAutomatedAnimationTest"));
    bAutomatedEnemyTest = FParse::Param(FCommandLine::Get(), TEXT("CFAutomatedEnemyTest"));
    SetShieldPresentation(false);
    SetBaseAnimation(IdleAnimation, true, 1.0f, 0.0f);
}

void ACFPlayerCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    FireCooldownRemaining = FMath::Max(0.0f, FireCooldownRemaining - DeltaSeconds);
    ShieldCooldownRemaining = FMath::Max(0.0f, ShieldCooldownRemaining - DeltaSeconds);
    DamageInvulnerabilityRemaining = FMath::Max(0.0f, DamageInvulnerabilityRemaining - DeltaSeconds);
    AnimationLockRemaining = FMath::Max(0.0f, AnimationLockRemaining - DeltaSeconds);
    MuzzleFlashRemaining = FMath::Max(0.0f, MuzzleFlashRemaining - DeltaSeconds);

    if (bAutomatedAnimationTest)
    {
        UpdateAutomatedAnimationTest(DeltaSeconds);
    }
    if (bAutomatedEnemyTest)
    {
        UpdateAutomatedEnemyTest(DeltaSeconds);
    }

    const bool bShieldWasActive = IsShieldActive();
    ShieldRemaining = FMath::Max(0.0f, ShieldRemaining - DeltaSeconds);
    if (bShieldWasActive && !IsShieldActive())
    {
        SetShieldPresentation(false);
        OnShieldVisualChanged(false);
    }

    UpdateCharacterPresentation(DeltaSeconds);

    if (GetActorLocation().Z < -500.0f)
    {
        TakeDamage(1.0f, FDamageEvent(), nullptr, nullptr);
    }
}

void ACFPlayerCharacter::UpdateAutomatedEnemyTest(float DeltaSeconds)
{
    AutomatedEnemyTestTime += DeltaSeconds;
    if (AutomatedEnemyTestStage == 0 && AutomatedEnemyTestTime >= 0.2f)
    {
        for (TActorIterator<ACFPatrolEnemy> It(GetWorld()); It; ++It)
        {
            const FVector EnemyLocation = It->GetActorLocation();
            SetActorLocation(FVector(EnemyLocation.X - 470.0f, GetActorLocation().Y, GetActorLocation().Z),
                false, nullptr, ETeleportType::TeleportPhysics);
            FacingDirection = 1.0f;
            AutomatedEnemyTestStage = 1;
            break;
        }
    }
    else if (AutomatedEnemyTestStage == 1 && AutomatedEnemyTestTime >= 0.78f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_EnemyWindup.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ENEMY_TEST Windup screenshot requested"));
        AutomatedEnemyTestStage = 2;
    }
    else if (AutomatedEnemyTestStage == 2 && AutomatedEnemyTestTime >= 1.08f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_EnemyRecoil.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ENEMY_TEST Recoil screenshot requested"));
        AutomatedEnemyTestStage = 3;
    }
    else if (AutomatedEnemyTestStage == 3 && AutomatedEnemyTestTime >= 2.2f)
    {
        UE_LOG(LogTemp, Display, TEXT("CF_ENEMY_TEST PASS"));
        bAutomatedEnemyTest = false;
        FPlatformMisc::RequestExit(false);
    }
}

void ACFPlayerCharacter::UpdateAutomatedAnimationTest(float DeltaSeconds)
{
    AutomatedTestTime += DeltaSeconds;
    if (AutomatedTestTime >= 0.65f && AutomatedTestTime < 2.45f)
    {
        FacingDirection = 1.0f;
        AddMovementInput(FVector::ForwardVector, 0.72f);
    }

    if (AutomatedTestStage == 0 && AutomatedTestTime >= 1.25f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_Run.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Run screenshot requested"));
        AutomatedTestStage = 1;
    }
    else if (AutomatedTestStage == 1 && AutomatedTestTime >= 1.65f)
    {
        FireInDirection(1.0f);
        AutomatedTestStage = 2;
    }
    else if (AutomatedTestStage == 2 && AutomatedTestTime >= 1.76f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_FireLayer.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Fire layer screenshot requested"));
        AutomatedTestStage = 3;
    }
    else if (AutomatedTestStage == 3 && AutomatedTestTime >= 2.65f)
    {
        StartJump();
        AutomatedTestStage = 4;
    }
    else if (AutomatedTestStage == 4 && AutomatedTestTime >= 2.9f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_JumpBlend.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Jump screenshot requested"));
        AutomatedTestStage = 5;
    }
    else if (AutomatedTestStage == 5 && AutomatedTestTime >= 3.75f)
    {
        ActivateShield();
        AutomatedTestStage = 6;
    }
    else if (AutomatedTestStage == 6 && AutomatedTestTime >= 4.02f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_Shield.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Shield screenshot requested"));
        AutomatedTestStage = 7;
    }
    else if (AutomatedTestStage == 7 && AutomatedTestTime >= 5.25f)
    {
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST PASS"));
        bAutomatedAnimationTest = false;
        FPlatformMisc::RequestExit(false);
    }
}

UAnimSequencerInstance* ACFPlayerCharacter::GetHeroAnimInstance() const
{
    return GetMesh() ? Cast<UAnimSequencerInstance>(GetMesh()->GetAnimInstance()) : nullptr;
}

void ACFPlayerCharacter::SetBaseAnimation(UAnimSequence* Animation, bool bLooping, float PlayRate,
    float BlendDuration)
{
    if (!Animation)
    {
        return;
    }

    if (Animation == CurrentBaseAnimation)
    {
        CurrentBasePlayRate = PlayRate;
        bCurrentBaseLooping = bLooping;
        return;
    }

    PreviousBaseAnimation = CurrentBaseAnimation;
    PreviousBaseTime = CurrentBaseTime;
    PreviousBasePlayRate = CurrentBasePlayRate;
    bPreviousBaseLooping = bCurrentBaseLooping;
    CurrentBaseAnimation = Animation;
    CurrentBaseTime = 0.0f;
    CurrentBasePlayRate = PlayRate;
    bCurrentBaseLooping = bLooping;
    CurrentBaseTrack = 1 - CurrentBaseTrack;
    BaseBlendElapsed = 0.0f;
    BaseBlendDuration = PreviousBaseAnimation ? FMath::Max(0.01f, BlendDuration) : 0.0f;
}

void ACFPlayerCharacter::TriggerAdditiveAnimation(UAnimSequence* Animation, float Duration, float PlayRate)
{
    if (!Animation)
    {
        return;
    }
    AdditiveAnimation = Animation;
    AdditiveTime = 0.0f;
    AdditiveDuration = FMath::Max(0.01f, Duration);
    AdditivePlayRate = PlayRate;
}

void ACFPlayerCharacter::TriggerCharacterAnimation(UAnimSequence* Animation, float LockDuration, float PlayRate)
{
    if (!Animation)
    {
        return;
    }
    AnimationLockRemaining = LockDuration;
    SetBaseAnimation(Animation, false, PlayRate, 0.08f);
}

void ACFPlayerCharacter::UpdateAnimationGraph(float DeltaSeconds)
{
    UAnimSequencerInstance* AnimInstance = GetHeroAnimInstance();
    if (!AnimInstance || !CurrentBaseAnimation)
    {
        return;
    }

    auto AdvanceTime = [DeltaSeconds](float& Time, UAnimSequence* Animation, float Rate, bool bLooping)
    {
        if (!Animation)
        {
            return;
        }
        const float Length = FMath::Max(Animation->GetPlayLength(), KINDA_SMALL_NUMBER);
        Time += DeltaSeconds * Rate;
        Time = bLooping ? FMath::Fmod(Time, Length) : FMath::Min(Time, Length);
    };

    AdvanceTime(CurrentBaseTime, CurrentBaseAnimation, CurrentBasePlayRate, bCurrentBaseLooping);
    AdvanceTime(PreviousBaseTime, PreviousBaseAnimation, PreviousBasePlayRate, bPreviousBaseLooping);
    BaseBlendElapsed += DeltaSeconds;
    const float BlendAlpha = BaseBlendDuration <= KINDA_SMALL_NUMBER
        ? 1.0f
        : FMath::Clamp(BaseBlendElapsed / BaseBlendDuration, 0.0f, 1.0f);

    AnimInstance->ResetNodes();
    const int32 PreviousTrack = 1 - CurrentBaseTrack;
    if (PreviousBaseAnimation && BlendAlpha < 1.0f)
    {
        AnimInstance->UpdateAnimTrack(PreviousBaseAnimation, PreviousTrack, PreviousBaseTime,
            1.0f - FMath::InterpEaseInOut(0.0f, 1.0f, BlendAlpha, 2.0f), false);
    }
    const float CurrentWeight = PreviousBaseAnimation
        ? FMath::InterpEaseInOut(0.0f, 1.0f, BlendAlpha, 2.0f)
        : 1.0f;
    AnimInstance->UpdateAnimTrack(CurrentBaseAnimation, CurrentBaseTrack, CurrentBaseTime, CurrentWeight, false);

    if (BlendAlpha >= 1.0f)
    {
        PreviousBaseAnimation = nullptr;
    }

    if (AdditiveAnimation)
    {
        AdditiveTime += DeltaSeconds * AdditivePlayRate;
        const float Remaining = AdditiveDuration - AdditiveTime;
        constexpr float BlendIn = 0.045f;
        constexpr float BlendOut = 0.075f;
        const float InWeight = FMath::Clamp(AdditiveTime / BlendIn, 0.0f, 1.0f);
        const float OutWeight = FMath::Clamp(Remaining / BlendOut, 0.0f, 1.0f);
        const float ActionWeight = FMath::Min(InWeight, OutWeight);
        if (Remaining > 0.0f)
        {
            const float SampleTime = FMath::Min(AdditiveTime, AdditiveAnimation->GetPlayLength());
            AnimInstance->UpdateAnimTrack(AdditiveAnimation, 2, SampleTime, ActionWeight, false);
        }
        else
        {
            AdditiveAnimation = nullptr;
            AdditiveTime = 0.0f;
        }
    }
}

void ACFPlayerCharacter::SetShieldPresentation(bool bActive)
{
    if (ShieldVisual)
    {
        ShieldVisual->SetVisibility(bActive, true);
    }
    if (ShieldLight)
    {
        ShieldLight->SetIntensity(bActive ? 2600.0f : 0.0f);
    }
}

void ACFPlayerCharacter::UpdateCharacterPresentation(float DeltaSeconds)
{
    USkeletalMeshComponent* CharacterVisual = GetMesh();
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (!CharacterVisual || !Movement)
    {
        return;
    }

    const FVector Velocity = GetVelocity();
    const float HorizontalSpeed = FMath::Abs(Velocity.X);
    const bool bGrounded = Movement->IsMovingOnGround();
    if (bGrounded && !bWasGrounded)
    {
        CameraLandingOffset = -24.0f;
        if (!IsShieldActive())
        {
            TriggerCharacterAnimation(LandAnimation, 0.26f, 1.0f);
        }
    }
    bWasGrounded = bGrounded;

    if (IsShieldActive())
    {
        SetBaseAnimation(ShieldAnimation, true, 1.0f, 0.1f);
    }
    else if (AnimationLockRemaining <= 0.0f)
    {
        if (!bGrounded)
        {
            SetBaseAnimation(Velocity.Z > 40.0f ? JumpRiseAnimation.Get() : JumpFallAnimation.Get(), true, 1.0f, 0.1f);
        }
        else if (bIsCrouched)
        {
            SetBaseAnimation(CrouchAnimation, true, 1.0f, 0.12f);
        }
        else if (HorizontalSpeed > 30.0f)
        {
            const float SpeedRatio = FMath::Clamp(HorizontalSpeed / Movement->MaxWalkSpeed, 0.0f, 1.0f);
            SetBaseAnimation(RunAnimation, true, FMath::Lerp(0.72f, 1.28f, SpeedRatio), 0.16f);
        }
        else
        {
            SetBaseAnimation(IdleAnimation, true, 1.0f, 0.18f);
        }
    }

    UpdateAnimationGraph(DeltaSeconds);

    const float SpeedRatio = FMath::Clamp(HorizontalSpeed / Movement->MaxWalkSpeed, 0.0f, 1.0f);
    const float GroundLean = -4.0f * SpeedRatio;
    const float AirLean = FMath::Clamp(-Velocity.Z / 180.0f, -7.0f, 7.0f);
    const float Lean = bGrounded ? GroundLean : AirLean;
    const float DirectionalYaw = FacingDirection > 0.0f ? -18.0f : 18.0f;
    const FRotator DesiredVisualRotation(0.0f, DirectionalYaw, Lean);
    CharacterVisual->SetRelativeLocation(FVector(0.0f, 0.0f, -92.0f));
    CharacterVisual->SetRelativeScale3D(FVector::OneVector);
    CharacterVisual->SetRelativeRotation(FMath::RInterpTo(
        CharacterVisual->GetRelativeRotation(), DesiredVisualRotation, DeltaSeconds, 12.0f));

    CameraLandingOffset = FMath::FInterpTo(CameraLandingOffset, 0.0f, DeltaSeconds, 9.0f);
    const float LookAhead = FMath::Clamp(Velocity.X / Movement->MaxWalkSpeed, -1.0f, 1.0f) * 95.0f;
    const FVector DesiredCameraOffset(LookAhead, 0.0f, 28.0f + CameraLandingOffset);
    CameraBoom->TargetOffset = FMath::VInterpTo(CameraBoom->TargetOffset, DesiredCameraOffset, DeltaSeconds, 5.5f);

    if (ShieldVisual && ShieldLight && IsShieldActive())
    {
        const float Pulse = 0.5f + 0.5f * FMath::Sin(GetWorld()->GetTimeSeconds() * 9.0f);
        ShieldVisual->SetRelativeScale3D(FVector(1.08f, 0.72f, 1.58f) * (1.0f + Pulse * 0.025f));
        ShieldVisual->AddLocalRotation(FRotator(0.0f, 38.0f * DeltaSeconds, 0.0f));
        ShieldLight->SetIntensity(1700.0f + 420.0f * Pulse);
    }
    if (MuzzleLight)
    {
        MuzzleLight->SetIntensity(MuzzleFlashRemaining > 0.0f ? 3200.0f : 0.0f);
    }
    if (MuzzleFlashVisual)
    {
        const bool bFlashVisible = MuzzleFlashRemaining > 0.0f;
        MuzzleFlashVisual->SetVisibility(bFlashVisible);
        if (bFlashVisible)
        {
            const float LifeAlpha = FMath::Clamp(MuzzleFlashRemaining / 0.075f, 0.0f, 1.0f);
            MuzzleFlashVisual->SetRelativeLocation(FVector(FacingDirection * 88.0f, -24.0f, 36.0f));
            MuzzleFlashVisual->SetRelativeRotation(
                FRotator(FacingDirection > 0.0f ? 90.0f : -90.0f, 0.0f, 0.0f));
            MuzzleFlashVisual->SetRelativeScale3D(
                FVector(0.08f, 0.08f, FMath::Lerp(0.22f, 0.38f, LifeAlpha)));
        }
    }
}

float ACFPlayerCharacter::TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent,
    AController* EventInstigator, AActor* DamageCauser)
{
    if (DamageAmount <= 0.0f || DamageInvulnerabilityRemaining > 0.0f || !CanAct())
    {
        return 0.0f;
    }

    const float AppliedDamage = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
    CurrentHealth = FMath::Max(0, CurrentHealth - FMath::Max(1, FMath::RoundToInt(DamageAmount)));
    DamageInvulnerabilityRemaining = 0.9f;
    TriggerCharacterAnimation(HitAnimation, 0.24f, 1.0f);
    OnHealthChanged(CurrentHealth, MaxHealth);
    if (CurrentHealth <= 0)
    {
        if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->PlayerDefeated();
    }
    else
    {
        ResetAtCheckpoint();
    }
    return AppliedDamage > 0.0f ? AppliedDamage : DamageAmount;
}

void ACFPlayerCharacter::ResetAtCheckpoint()
{
    GetCharacterMovement()->StopMovementImmediately();
    SetActorLocation(CheckpointLocation, false, nullptr, ETeleportType::TeleportPhysics);
}

void ACFPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ACFPlayerCharacter::MoveRight);
    PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &ACFPlayerCharacter::StartJump);
    PlayerInputComponent->BindAction(TEXT("Jump"), IE_Released, this, &ACFPlayerCharacter::StopJump);
    PlayerInputComponent->BindAction(TEXT("Crouch"), IE_Pressed, this, &ACFPlayerCharacter::StartCrouch);
    PlayerInputComponent->BindAction(TEXT("Crouch"), IE_Released, this, &ACFPlayerCharacter::StopCrouch);
    PlayerInputComponent->BindAction(TEXT("Fire"), IE_Pressed, this, &ACFPlayerCharacter::FirePulse);
    PlayerInputComponent->BindAction(TEXT("FireLeft"), IE_Pressed, this, &ACFPlayerCharacter::FireLeft);
    PlayerInputComponent->BindAction(TEXT("FireRight"), IE_Pressed, this, &ACFPlayerCharacter::FireRight);
    PlayerInputComponent->BindAction(TEXT("Shield"), IE_Pressed, this, &ACFPlayerCharacter::ActivateShield);
    FInputActionBinding& PauseBinding = PlayerInputComponent->BindAction(TEXT("Pause"), IE_Pressed, this, &ACFPlayerCharacter::TogglePause);
    PauseBinding.bExecuteWhenPaused = true;
    FInputActionBinding& RestartBinding = PlayerInputComponent->BindAction(TEXT("Restart"), IE_Pressed, this, &ACFPlayerCharacter::RestartLevel);
    RestartBinding.bExecuteWhenPaused = true;
    FInputActionBinding& CampaignBinding = PlayerInputComponent->BindAction(TEXT("RestartCampaign"), IE_Pressed, this, &ACFPlayerCharacter::RestartCampaign);
    CampaignBinding.bExecuteWhenPaused = true;
}

void ACFPlayerCharacter::MoveRight(float Value)
{
    if (FMath::IsNearlyZero(Value) || IsShieldActive() || !CanAct())
    {
        return;
    }

    FacingDirection = FMath::Sign(Value);
    AddMovementInput(FVector::ForwardVector, Value);
}

void ACFPlayerCharacter::StartJump()
{
    if (!IsShieldActive() && CanAct())
    {
        TriggerCharacterAnimation(JumpStartAnimation, 0.19f, 1.0f);
        Jump();
    }
}

void ACFPlayerCharacter::StopJump()
{
    StopJumping();
}

void ACFPlayerCharacter::StartCrouch()
{
    if (!IsShieldActive() && CanAct())
    {
        Crouch();
    }
}

void ACFPlayerCharacter::StopCrouch()
{
    UnCrouch();
}

void ACFPlayerCharacter::FirePulse()
{
    FireInDirection(FacingDirection);
}

void ACFPlayerCharacter::FireLeft()
{
    FireInDirection(-1.0f);
}

void ACFPlayerCharacter::FireRight()
{
    FireInDirection(1.0f);
}

void ACFPlayerCharacter::FireInDirection(float Direction)
{
    if (FireCooldownRemaining > 0.0f || IsShieldActive() || ProjectileClass == nullptr || !CanAct())
    {
        return;
    }

    FacingDirection = FMath::Sign(Direction);
    FireCooldownRemaining = FireCooldown;
    MuzzleFlashRemaining = 0.075f;
    TriggerAdditiveAnimation(FireAnimation, 0.22f, 1.0f);
    const FVector SpawnLocation = GetActorLocation() + FVector(FacingDirection * 90.0f, 0.0f, 35.0f);
    const FRotator SpawnRotation(0.0f, FacingDirection > 0.0f ? 0.0f : 180.0f, 0.0f);
    if (MuzzleLight)
    {
        MuzzleLight->SetRelativeLocation(FVector(FacingDirection * 72.0f, -24.0f, 36.0f));
    }

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.Owner = this;
    SpawnParameters.Instigator = this;
    SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    GetWorld()->SpawnActor<ACFPulseProjectile>(ProjectileClass, SpawnLocation, SpawnRotation, SpawnParameters);
    if (MuzzleFlashSystem)
    {
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, MuzzleFlashSystem, SpawnLocation,
            SpawnRotation, FVector(0.12f));
    }
    OnPulseFired();
}

void ACFPlayerCharacter::ActivateShield()
{
    if (ShieldCooldownRemaining > 0.0f || IsShieldActive() || !CanAct())
    {
        return;
    }

    ShieldRemaining = ShieldDuration;
    ShieldCooldownRemaining = ShieldCooldown;
    AnimationLockRemaining = 0.0f;
    SetShieldPresentation(true);
    SetBaseAnimation(ShieldAnimation, true, 1.0f, 0.1f);
    OnShieldVisualChanged(true);
}

bool ACFPlayerCharacter::AbsorbProjectile(const FVector& ImpactLocation)
{
    if (!IsShieldActive()) return false;
    if (ShieldAbsorbSystem)
    {
        const FVector SpawnLocation = ImpactLocation.IsNearlyZero()
            ? GetActorLocation() + FVector(0.0f, 0.0f, 25.0f)
            : ImpactLocation;
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ShieldAbsorbSystem, SpawnLocation,
            FRotator::ZeroRotator, FVector(0.22f));
    }
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>())
    {
        if (UCFGameInstance* Instance = Cast<UCFGameInstance>(State->GetGameInstance())) Instance->AddBits(10);
    }
    return true;
}

float ACFPlayerCharacter::GetShieldReadyFraction() const
{
    return IsShieldActive() ? ShieldRemaining / ShieldDuration : 1.0f - ShieldCooldownRemaining / ShieldCooldown;
}

bool ACFPlayerCharacter::CanAct() const
{
    const ACFGameState* State = GetWorld() ? GetWorld()->GetGameState<ACFGameState>() : nullptr;
    return !State || State->CanPlayerAct();
}

void ACFPlayerCharacter::TogglePause()
{
    const bool bPaused = UGameplayStatics::IsGamePaused(this);
    UGameplayStatics::SetGamePaused(this, !bPaused);
}

void ACFPlayerCharacter::RestartLevel()
{
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->RestartCurrentLevel();
}

void ACFPlayerCharacter::RestartCampaign()
{
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->RestartCampaign();
}
