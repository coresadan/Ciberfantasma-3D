#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CFMovingPlatform.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

UCLASS()
class CIBERFANTASMA3D_API ACFMovingPlatform : public AActor
{
    GENERATED_BODY()

public:
    ACFMovingPlatform();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, Category = "Movement")
    bool bHorizontal = true;
    UPROPERTY(EditAnywhere, Category = "Movement")
    float MovementRange = 200.0f;
    UPROPERTY(EditAnywhere, Category = "Movement")
    float MovementSpeed = 1.25f;
    UPROPERTY(EditAnywhere, Category = "Movement")
    float PhaseOffset = 0.0f;
    UPROPERTY(EditAnywhere, Category = "Movement")
    bool bPhasePlatform = false;

private:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UBoxComponent> Collision;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Visual;
    FVector Origin;
};
