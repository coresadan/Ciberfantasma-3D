#include "CFGameState.h"

#include "CFGameInstance.h"
#include "Kismet/GameplayStatics.h"

namespace
{
    const FName CampaignMaps[] = {
        TEXT("Act01_Rooftops"), TEXT("Act02_DataCenter"), TEXT("Act03_ExecutiveCore"),
        TEXT("Act04_MemoryGardens"), TEXT("Act05_ConsensusFactory"), TEXT("Act06_SingleArchive"),
        TEXT("Act07_DeadIdeasAvenue"), TEXT("Act08_SilenceOffice"), TEXT("Act09_DirectorOffice")
    };
}

ACFGameState::ACFGameState()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ACFGameState::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    MessageRemaining = FMath::Max(0.0f, MessageRemaining - DeltaSeconds);
    LevelCardRemaining = FMath::Max(0.0f, LevelCardRemaining - DeltaSeconds);
}

void ACFGameState::CollectShard()
{
    CollectedShards = FMath::Min(CollectedShards + 1, RequiredShards);
    if (UCFGameInstance* Instance = GetGameInstance<UCFGameInstance>()) Instance->AddBits(100);
    ShowMessage(FString::Printf(TEXT("FRAGMENTO LIBERADO // %d/%d"), CollectedShards, RequiredShards));
    if (HasAllShards()) ShowMessage(TEXT("REPOSITORIO COMPLETO // SALIDA DESBLOQUEADA"), 3.0f);
    OnShardCountChanged(CollectedShards, RequiredShards);
}

void ACFGameState::HackTerminal()
{
    ++HackedTerminals;
    if (UCFGameInstance* Instance = GetGameInstance<UCFGameInstance>()) Instance->AddBits(250);
    ShowMessage(TEXT("CHECKPOINT SEGURO // IDENTIDAD ENMASCARADA"), 3.0f);
}

void ACFGameState::ConfigureLevel(int32 InLevelIndex, const FString& InName, const FString& InTitle)
{
    LevelIndex = FMath::Clamp(InLevelIndex, 0, 8);
    LevelName = InName;
    LevelTitle = InTitle;
    if (UCFGameInstance* Instance = GetGameInstance<UCFGameInstance>())
    {
        if (!Instance->bCampaignStarted) Instance->StartCampaign(LevelIndex);
        Instance->CurrentLevelIndex = LevelIndex;
    }
}

void ACFGameState::RegisterEnemy(bool bBoss)
{
    ++LivingEnemies;
    if (bBoss) ++LivingBosses;
}

void ACFGameState::EnemyDefeated(bool bBoss)
{
    LivingEnemies = FMath::Max(0, LivingEnemies - 1);
    if (bBoss) LivingBosses = FMath::Max(0, LivingBosses - 1);
    if (UCFGameInstance* Instance = GetGameInstance<UCFGameInstance>())
    {
        Instance->AddKill();
        Instance->AddBits(bBoss ? 2500 : 180);
    }
    if (bBoss) ShowMessage(TEXT("JEFE DESCOMPILADO // EL NUCLEO ES PUBLICO"), 3.5f);
}

void ACFGameState::PlayerDefeated()
{
    if (RunState != ECFRunState::Playing) return;
    RunState = ECFRunState::Defeat;
    UGameplayStatics::SetGamePaused(this, true);
}

void ACFGameState::CompleteLevel()
{
    if (!CanExit()) return;
    RunState = ECFRunState::Transitioning;
    if (LevelIndex >= 8)
    {
        RunState = ECFRunState::Victory;
        UGameplayStatics::SetGamePaused(this, true);
        return;
    }
    if (UCFGameInstance* Instance = GetGameInstance<UCFGameInstance>()) Instance->CurrentLevelIndex = LevelIndex + 1;
    UGameplayStatics::OpenLevel(this, CampaignMaps[LevelIndex + 1]);
}

void ACFGameState::ShowMessage(const FString& Message, float Duration)
{
    StatusMessage = Message;
    MessageRemaining = Duration;
}

void ACFGameState::RestartCurrentLevel()
{
    UGameplayStatics::SetGamePaused(this, false);
    UGameplayStatics::OpenLevel(this, CampaignMaps[FMath::Clamp(LevelIndex, 0, 8)]);
}

void ACFGameState::RestartCampaign()
{
    UGameplayStatics::SetGamePaused(this, false);
    if (UCFGameInstance* Instance = GetGameInstance<UCFGameInstance>()) Instance->StartCampaign(0);
    UGameplayStatics::OpenLevel(this, CampaignMaps[0]);
}

int32 ACFGameState::GetTotalBits() const
{
    const UCFGameInstance* Instance = GetGameInstance<UCFGameInstance>();
    return Instance ? Instance->TotalBits : 0;
}

int32 ACFGameState::GetTotalKills() const
{
    const UCFGameInstance* Instance = GetGameInstance<UCFGameInstance>();
    return Instance ? Instance->TotalKills : 0;
}
