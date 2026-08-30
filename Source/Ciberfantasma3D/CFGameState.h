#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "CFGameState.generated.h"

UENUM(BlueprintType)
enum class ECFRunState : uint8
{
    Playing,
    Transitioning,
    Victory,
    Defeat
};

UCLASS()
class CIBERFANTASMA3D_API ACFGameState : public AGameStateBase
{
    GENERATED_BODY()

public:
    ACFGameState();
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Ciberfantasma|Progress")
    void CollectShard();

    void HackTerminal();
    void ConfigureLevel(int32 InLevelIndex, const FString& InName, const FString& InTitle);
    void RegisterEnemy(bool bBoss);
    void EnemyDefeated(bool bBoss);
    void PlayerDefeated();
    void CompleteLevel();
    void ShowMessage(const FString& Message, float Duration = 2.5f);
    void RestartCurrentLevel();
    void RestartCampaign();

    int32 GetTotalBits() const;
    int32 GetTotalKills() const;

    UFUNCTION(BlueprintPure, Category = "Ciberfantasma|Progress")
    bool HasAllShards() const { return CollectedShards >= RequiredShards; }

    bool CanExit() const { return HasAllShards() && LivingBosses == 0 && RunState == ECFRunState::Playing; }
    bool CanPlayerAct() const { return RunState == ECFRunState::Playing; }

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    int32 RequiredShards = 3;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    int32 CollectedShards = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    int32 HackedTerminals = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    int32 LivingBosses = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    int32 LivingEnemies = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    int32 LevelIndex = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    FString LevelName = TEXT("ACTO I");

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    FString LevelTitle = TEXT("AZOTEAS DEL MONOPOLIO");

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Ciberfantasma|Progress")
    ECFRunState RunState = ECFRunState::Playing;

    FString StatusMessage;
    float MessageRemaining = 0.0f;
    float LevelCardRemaining = 3.2f;

protected:
    UFUNCTION(BlueprintImplementableEvent, Category = "Ciberfantasma|Presentation")
    void OnShardCountChanged(int32 Current, int32 Required);
};
