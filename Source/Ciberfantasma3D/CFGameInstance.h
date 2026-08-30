#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "CFGameInstance.generated.h"

UCLASS()
class CIBERFANTASMA3D_API UCFGameInstance : public UGameInstance
{
    GENERATED_BODY()

public:
    void StartCampaign(int32 StartLevel = 0);
    void AddBits(int32 Amount) { TotalBits = FMath::Max(0, TotalBits + Amount); }
    void AddKill() { ++TotalKills; }

    int32 CurrentLevelIndex = 0;
    int32 TotalBits = 0;
    int32 TotalKills = 0;
    double CampaignStartSeconds = 0.0;
    bool bCampaignStarted = false;
};
