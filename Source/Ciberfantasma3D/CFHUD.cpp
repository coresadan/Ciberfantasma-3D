#include "CFHUD.h"

#include "CFGameInstance.h"
#include "CFGameState.h"
#include "CFPlayerCharacter.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "HAL/PlatformTime.h"

void ACFHUD::DrawHUD()
{
    Super::DrawHUD();
    if (!Canvas || !GEngine) return;
    const ACFGameState* State = GetWorld()->GetGameState<ACFGameState>();
    const ACFPlayerCharacter* Player = Cast<ACFPlayerCharacter>(GetOwningPawn());
    if (!State || !Player) return;

    UFont* Font = GEngine->GetMediumFont();
    UFont* Small = GEngine->GetSmallFont();
    const float W = Canvas->SizeX;
    DrawRect(FLinearColor(0.005f, 0.015f, 0.025f, 0.88f), 22.0f, 20.0f, 560.0f, 88.0f);
    DrawText(State->LevelName, FLinearColor(0.2f, 0.9f, 1.0f), 40.0f, 31.0f, Small, 1.0f);
    DrawText(State->LevelTitle, FLinearColor::White, 40.0f, 53.0f, Font, 1.0f);

    DrawText(TEXT("VIDA"), FLinearColor(0.5f, 0.8f, 0.9f), 620.0f, 27.0f, Small);
    for (int32 Index = 0; Index < Player->GetMaxHealth(); ++Index)
    {
        DrawRect(Index < Player->GetCurrentHealth() ? FLinearColor(0.1f, 1.0f, 0.32f) : FLinearColor(0.12f, 0.18f, 0.2f),
            620.0f + Index * 35.0f, 52.0f, 26.0f, 22.0f);
    }
    DrawText(FString::Printf(TEXT("FRAGMENTOS %d/%d"), State->CollectedShards, State->RequiredShards),
        FLinearColor(0.2f, 1.0f, 0.4f), 760.0f, 31.0f, Font);
    DrawText(FString::Printf(TEXT("BITS %06d"), State->GetTotalBits()), FLinearColor(0.2f, 0.9f, 1.0f), W - 230.0f, 31.0f, Font);
    DrawText(FString::Printf(TEXT("ESCUDO L  %d%%"), FMath::RoundToInt(Player->GetShieldReadyFraction() * 100.0f)),
        Player->IsShieldActive() ? FLinearColor::White : FLinearColor(0.45f, 0.8f, 1.0f), 620.0f, 82.0f, Small);

    DrawText(TEXT("A/D MOVER   ESPACIO DOBLE SALTO   S AGACHARSE   J/K/X DISPARAR   L ESCUDO   P PAUSA   R REINICIAR"),
        FLinearColor(0.45f, 0.65f, 0.72f), 28.0f, Canvas->SizeY - 36.0f, Small, 0.9f);

    if (State->LevelCardRemaining > 0.0f)
    {
        DrawRect(FLinearColor(0.0f, 0.0f, 0.0f, 0.72f), W * 0.19f, Canvas->SizeY * 0.37f, W * 0.62f, 150.0f);
        DrawText(State->LevelName, FLinearColor(0.2f, 1.0f, 0.4f), W * 0.25f, Canvas->SizeY * 0.4f, Font, 1.2f);
        DrawText(State->LevelTitle, FLinearColor::White, W * 0.25f, Canvas->SizeY * 0.46f, Font, 1.5f);
    }
    if (!State->StatusMessage.IsEmpty() && State->MessageRemaining > 0.0f)
    {
        DrawRect(FLinearColor(0.0f, 0.03f, 0.05f, 0.9f), W * 0.25f, Canvas->SizeY - 115.0f, W * 0.5f, 45.0f);
        DrawText(State->StatusMessage, FLinearColor(0.4f, 1.0f, 0.85f), W * 0.28f, Canvas->SizeY - 105.0f, Small, 1.0f);
    }
    if (State->RunState != ECFRunState::Playing)
    {
        DrawRect(FLinearColor(0.0f, 0.0f, 0.0f, 0.9f), 0.0f, 0.0f, Canvas->SizeX, Canvas->SizeY);
        const bool bVictory = State->RunState == ECFRunState::Victory;
        DrawText(bVictory ? TEXT("LA CREATIVIDAD ES LIBRE") : TEXT("SESION INTERRUMPIDA"),
            bVictory ? FLinearColor(0.2f, 1.0f, 0.4f) : FLinearColor(1.0f, 0.08f, 0.2f), W * 0.3f, Canvas->SizeY * 0.38f, Font, 2.0f);
        DrawText(FString::Printf(TEXT("PUNTOS %06d   ENEMIGOS %d"), State->GetTotalBits(), State->GetTotalKills()),
            FLinearColor::White, W * 0.38f, Canvas->SizeY * 0.51f, Font);
        DrawText(TEXT("ENTER: NUEVA CAMPANA    R: REINTENTAR ACTO"), FLinearColor(0.3f, 0.9f, 1.0f), W * 0.35f, Canvas->SizeY * 0.6f, Small);
    }
}
