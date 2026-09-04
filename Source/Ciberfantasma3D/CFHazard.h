#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CFHazard.generated.h"

class UBoxComponent;
class UPointLightComponent;
class UPrimitiveComponent;
class UStaticMeshComponent;

UCLASS()
class CIBERFANTASMA3D_API ACFHazard : public AActor
{
    GENERATED_BODY()

public:
    ACFHazard();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, Category = "Hazard")
    FName HazardStyle = TEXT("spikes");

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
    TObjectPtr<UStaticMeshComponent> DetailA;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> DetailB;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UPointLightComponent> Glow;
};
