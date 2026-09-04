#include "CFHeroAnimInstance.h"

#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimTypes.h"
#include "TwoBoneIK.h"
#include "BonePose.h"

namespace
{
bool ResolveCompactBone(const FBoneContainer& BoneContainer, const FName BoneName,
    FCompactPoseBoneIndex& OutBoneIndex)
{
    const int32 PoseBoneIndex = BoneContainer.GetPoseBoneIndexForBoneName(BoneName);
    if (PoseBoneIndex == INDEX_NONE)
    {
        return false;
    }

    OutBoneIndex = BoneContainer.MakeCompactPoseIndex(FMeshPoseBoneIndex(PoseBoneIndex));
    return OutBoneIndex != INDEX_NONE;
}

void SolveGroundedLeg(FCSPose<FCompactPose>& ComponentPose, const FBoneContainer& BoneContainer,
    const FName ThighName, const FName CalfName, const FName FootName,
    const FVector& EffectorOffset, const FQuat& FootRotationDelta, const float Alpha)
{
    FCompactPoseBoneIndex ThighIndex;
    FCompactPoseBoneIndex CalfIndex;
    FCompactPoseBoneIndex FootIndex;
    if (!ResolveCompactBone(BoneContainer, ThighName, ThighIndex)
        || !ResolveCompactBone(BoneContainer, CalfName, CalfIndex)
        || !ResolveCompactBone(BoneContainer, FootName, FootIndex))
    {
        return;
    }

    FTransform ThighTransform = ComponentPose.GetComponentSpaceTransform(ThighIndex);
    FTransform CalfTransform = ComponentPose.GetComponentSpaceTransform(CalfIndex);
    FTransform FootTransform = ComponentPose.GetComponentSpaceTransform(FootIndex);
    const FVector Effector = FootTransform.GetLocation() + EffectorOffset;

    // The authored legs bend towards component-local -Y (the character's
    // sagittal/front plane). Keeping the target near the animated knee avoids
    // knee flips when the player turns through a three-quarter presentation.
    const FVector JointTarget = CalfTransform.GetLocation() + FVector(0.0f, -48.0f, 2.0f);
    AnimationCore::SolveTwoBoneIK(ThighTransform, CalfTransform, FootTransform,
        JointTarget, Effector, false, 1.0, 1.0);
    FootTransform.SetRotation((FootRotationDelta * FootTransform.GetRotation()).GetNormalized());

    const TArray<FBoneTransform> SolvedBones = {
        FBoneTransform(ThighIndex, ThighTransform),
        FBoneTransform(CalfIndex, CalfTransform),
        FBoneTransform(FootIndex, FootTransform)
    };
    ComponentPose.LocalBlendCSBoneTransforms(SolvedBones, Alpha);
}
}

void FCFHeroAnimInstanceProxy::SetFootGrounding(const float InAlpha, const float InPelvisOffset,
    const FVector& InLeftFootOffset, const FQuat& InLeftFootRotation,
    const FVector& InRightFootOffset, const FQuat& InRightFootRotation)
{
    GroundingAlpha = FMath::Clamp(InAlpha, 0.0f, 1.0f);
    PelvisOffset = InPelvisOffset;
    LeftFootOffset = InLeftFootOffset;
    RightFootOffset = InRightFootOffset;
    LeftFootRotation = InLeftFootRotation;
    RightFootRotation = InRightFootRotation;
}

bool FCFHeroAnimInstanceProxy::Evaluate(FPoseContext& Output)
{
    const bool bEvaluated = FAnimSequencerInstanceProxy::Evaluate(Output);
    if (!bEvaluated || GroundingAlpha <= ZERO_ANIMWEIGHT_THRESH)
    {
        return bEvaluated;
    }

    const FBoneContainer& BoneContainer = Output.Pose.GetBoneContainer();
    FCSPose<FCompactPose> ComponentPose;
    ComponentPose.InitPose(Output.Pose);

    FCompactPoseBoneIndex PelvisIndex;
    if (ResolveCompactBone(BoneContainer, TEXT("pelvis"), PelvisIndex))
    {
        FTransform PelvisTransform = ComponentPose.GetComponentSpaceTransform(PelvisIndex);
        PelvisTransform.AddToTranslation(FVector(0.0f, 0.0f, PelvisOffset));
        const TArray<FBoneTransform> PelvisBone = {FBoneTransform(PelvisIndex, PelvisTransform)};
        ComponentPose.LocalBlendCSBoneTransforms(PelvisBone, GroundingAlpha);
    }

    SolveGroundedLeg(ComponentPose, BoneContainer, TEXT("thigh_l"), TEXT("calf_l"), TEXT("foot_l"),
        LeftFootOffset, LeftFootRotation, GroundingAlpha);
    SolveGroundedLeg(ComponentPose, BoneContainer, TEXT("thigh_r"), TEXT("calf_r"), TEXT("foot_r"),
        RightFootOffset, RightFootRotation, GroundingAlpha);

    FCSPose<FCompactPose>::ConvertComponentPosesToLocalPoses(MoveTemp(ComponentPose), Output.Pose);
    return true;
}

UCFHeroAnimInstance::UCFHeroAnimInstance(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    // The player pushes trace results immediately before pose evaluation. The
    // parent already uses game-thread evaluation; make the contract explicit.
    bUseMultiThreadedAnimationUpdate = false;
}

FAnimInstanceProxy* UCFHeroAnimInstance::CreateAnimInstanceProxy()
{
    return new FCFHeroAnimInstanceProxy(this);
}

void UCFHeroAnimInstance::SetFootGrounding(const float Alpha, const float InPelvisOffset,
    const FVector& InLeftFootOffset, const FQuat& InLeftFootRotation,
    const FVector& InRightFootOffset, const FQuat& InRightFootRotation)
{
    GetProxyOnGameThread<FCFHeroAnimInstanceProxy>().SetFootGrounding(
        Alpha, InPelvisOffset, InLeftFootOffset, InLeftFootRotation,
        InRightFootOffset, InRightFootRotation);
}
