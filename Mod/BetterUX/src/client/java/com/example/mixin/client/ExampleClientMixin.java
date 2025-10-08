package com.example.mixin.client;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.hud.ChatHud;
import net.minecraft.client.network.ClientPlayNetworkHandler;
import net.minecraft.network.packet.s2c.play.TitleS2CPacket;
import net.minecraft.network.packet.s2c.play.SubtitleS2CPacket;
import net.minecraft.registry.RegistryWrapper;
import net.minecraft.text.Text;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.Objects;

@Mixin(ClientPlayNetworkHandler.class)
public class ExampleClientMixin {

    @Unique
    private static final String[] RECORD_TEXT = {"우승", "완주"};

    @Unique
    private boolean textDetected = false; // 한 번만 감지

    @Unique
    private int resetTicks = 0; // tick 기반 플래그 초기화

    @Unique
    private String latestTitle = null; // title 값을 저장

    @Unique
    private String latestSubtitle = null; // subtitle 값을 저장

    @Inject(method = "onTitle", at = @At("HEAD"))
    private void onTitle(TitleS2CPacket packet, CallbackInfo ci) {
        if (packet == null) return;

        Text titleText = packet.text();
        if (titleText == null) return;

        String plain = titleText.getString();
        if (plain == null) return;

        for (String record : RECORD_TEXT) {
            if (plain.equals(record)) {

                latestTitle = plain;

                break;
            }
        }
    }
    @Inject(method = "onSubtitle", at = @At("HEAD"))
    private void onSubtitle(SubtitleS2CPacket packet, CallbackInfo ci1) {
        if (Objects.equals(latestTitle, "우승") || Objects.equals(latestTitle, "완주")) {
            if (packet == null) return;

            Text SubtitleText = packet.text();
            if (SubtitleText == null || textDetected) return;

            String plainSub = SubtitleText.getString();
            textDetected = true; // 한 번만 감지
            resetTicks = 60; // 60 ticks = 약 3초 후 초기화
            System.out.println("plainSub : " + plainSub);
            latestSubtitle = plainSub; // 클래스 필드에 저장
            if (plainSub != null && plainSub.matches("\\d{2}:\\d{2}\\.\\d{3}")) {
                sendRecordSaveMessage();
            }
        }
    }

    private static String jsonEscape(String text) {
        return text.replace("\\", "\\\\").replace("\"", "\\\"");
    }
    @Unique
    private void sendRecordSaveMessage() {
        MinecraftClient client = MinecraftClient.getInstance();
        if (client.getNetworkHandler() == null) return;
        System.out.println("latestSubtitle : " + latestSubtitle);
        String safeText = jsonEscape(latestSubtitle);

        System.out.println("safeText : " + safeText);


        String jsonText = """
    [
        {"bold":true,"color":"#98FB98","text":"========================================="},
        {"color":"white","text":"\\n새로운 기록을 ","bold":false},
        {"color":"green","text":"업로드","bold":false},
        {"color":"white","text":"하시겠습니까?","bold":false},
        {"color":"yellow","text":"\\n\\n기록 : ","bold":false},
        {"text":"%s","color":"aqua","bold":false},
        {"color":"red","text":"\\n[ X ]","click_event":{"action":"run_command","command":"tellraw @s {\\"text\\":\\"거절 이벤트\\",\\"color\\":\\"red\\"}"}},
        {"text":"    "},
        {"color":"green","text":"[ O ]","click_event":{"action":"run_command","command":"tellraw @s {\\"text\\":\\"저장 이벤트\\",\\"color\\":\\"green\\"}"}},
        {"bold":true,"color":"#98FB98","text":"\\n========================================="}
    ]
    """.formatted(safeText);


        RegistryWrapper.WrapperLookup registries = client.getNetworkHandler().getRegistryManager();
        Text text = Text.Serialization.fromLenientJson(jsonText, registries);

        client.execute(() -> {
            if (client.inGameHud != null) {
                ChatHud chatHud = client.inGameHud.getChatHud();
                chatHud.addMessage(text);
            }
        });
    }

    // 매 tick마다 플래그 초기화 체크
    @Inject(method = "tick", at = @At("HEAD"))
    private void onTick(CallbackInfo ci) {
        if (textDetected && resetTicks > 0) {
            resetTicks--;
            if (resetTicks <= 0) {
                textDetected = false; // 플래그 초기화
            }
        }
    }
}