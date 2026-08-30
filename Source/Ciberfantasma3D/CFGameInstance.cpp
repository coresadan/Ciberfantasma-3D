#include "CFGameInstance.h"
#include "HAL/PlatformTime.h"

void UCFGameInstance::StartCampaign(int32 StartLevel)
{
    CurrentLevelIndex = FMath::Clamp(StartLevel, 0, 8);
    TotalBits = 0;
    TotalKills = 0;
    CampaignStartSeconds = FPlatformTime::Seconds();
    bCampaignStarted = true;
}
