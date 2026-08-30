#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CFExitPortal.generated.h"

class UCapsuleComponent;
class UPointLightComponent;
class UPrimitiveComponent;
class UStaticMeshComponent;

UCLASS()
class CIBERFANTASMA3D_API ACFExitPortal : public AActor
{
    GENERATED_BODY()

public:
    ACFExitPortal();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Campaign")
    int32 LevelIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Campaign")
    FString LevelName = TEXT("ACTO I");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Campaign")
    FString LevelTitle = TEXT("AZOTEAS DEL MONOPOLIO");

protected:
    UFUNCTION(BlueprintImplementableEvent, Category = "Ciberfantasma|Presentation")
    void OnPortalUnlocked();

    UFUNCTION(BlueprintImplementableEvent, Category = "Ciberfantasma|Presentation")
    void OnLevelCompleted();

private:
    UFUNCTION()
    void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UCapsuleComponent> Trigger;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Visual;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UPointLightComponent> Glow;

    bool bUnlocked = false;
    bool bCompleted = false;
};
