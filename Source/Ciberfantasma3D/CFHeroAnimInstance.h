#pragma once

#include "CoreMinimal.h"
#include "AnimSequencerInstance.h"
#include "AnimSequencerInstanceProxy.h"
#include "CFHeroAnimInstance.generated.h"

/**
 * Final-pose grounding pass for Ciberfantasma.
 *
 * The project intentionally keeps the lightweight sequencer player used by the
 * existing locomotion/action mixer. This proxy adds the production foot-IK pass
 * after that graph has evaluated, which means firing, shielding and locomotion
 * transitions all benefit from grounding without having to duplicate the graph.
 */
struct CIBERFANTASMA3D_API FCFHeroAnimInstanceProxy final : public FAnimSequencerInstanceProxy
{
    FCFHeroAnimInstanceProxy() = default;
    explicit FCFHeroAnimInstanceProxy(UAnimInstance* InAnimInstance)
        : FAnimSequencerInstanceProxy(InAnimInstance)
    {
    }

    virtual bool Evaluate(FPoseContext& Output) override;

    void SetFootGrounding(float InAlpha, float InPelvisOffset,
        const FVector& InLeftFootOffset, const FQuat& InLeftFootRotation,
        const FVector& InRightFootOffset, const FQuat& InRightFootRotation);

private:
    float GroundingAlpha = 0.0f;
    float PelvisOffset = 0.0f;
    FVector LeftFootOffset = FVector::ZeroVector;
    FVector RightFootOffset = FVector::ZeroVector;
    FQuat LeftFootRotation = FQuat::Identity;
    FQuat RightFootRotation = FQuat::Identity;
};

UCLASS(Transient, NotBlueprintable)
class CIBERFANTASMA3D_API UCFHeroAnimInstance final : public UAnimSequencerInstance
{
    GENERATED_BODY()

public:
    UCFHeroAnimInstance(const FObjectInitializer& ObjectInitializer);

    void SetFootGrounding(float Alpha, float PelvisOffset,
        const FVector& LeftFootOffset, const FQuat& LeftFootRotation,
        const FVector& RightFootOffset, const FQuat& RightFootRotation);

protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
};
