#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CFShard.generated.h"

class UPointLightComponent;
class UPrimitiveComponent;
class USphereComponent;
class UStaticMeshComponent;

UCLASS()
class CIBERFANTASMA3D_API ACFShard : public AActor
{
    GENERATED_BODY()

public:
    ACFShard();
    virtual void Tick(float DeltaSeconds) override;

protected:
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USphereComponent> Trigger;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Visual;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UPointLightComponent> Glow;

    float InitialZ = 0.0f;
    float TimeOffset = 0.0f;
};
