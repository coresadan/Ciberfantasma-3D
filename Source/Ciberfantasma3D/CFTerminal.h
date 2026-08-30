#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CFTerminal.generated.h"

class UBoxComponent;
class UPointLightComponent;
class UStaticMeshComponent;

UCLASS()
class CIBERFANTASMA3D_API ACFTerminal : public AActor
{
    GENERATED_BODY()

public:
    ACFTerminal();

private:
    UFUNCTION()
    void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UBoxComponent> Trigger;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UPointLightComponent> Glow;
    bool bHacked = false;
};
