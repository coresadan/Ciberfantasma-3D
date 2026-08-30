#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "CFHUD.generated.h"

UCLASS()
class CIBERFANTASMA3D_API ACFHUD : public AHUD
{
    GENERATED_BODY()

public:
    virtual void DrawHUD() override;
};
