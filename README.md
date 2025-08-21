<img width="180" height="180" alt="clock" src="https://github.com/user-attachments/assets/436dcff9-bd5d-49f5-a6d9-b5df92a73d27" />


# McriderBot
도로주행 기능사 로봇 (디스코드 봇)

구글 스프레드시트를 이용한 프로그램으로, 유저들의 주행 기록과 탑승 카트, 엔진이 포함된 데이터가 스프레드시트에 저장되고, 이를 주행 기록을 기준으로 오름차순 정리하여 순위를 나타내는 방식을 사용합니다.

Made By bkgpolar12, hexx-4, Migan178

## 베리파이어 역할
기록을 등록하거나 기록 신청을 거절하는 역할로, 봇의 동작 과정에 필요한 역할입니다.

## 커맨드
+ /addrecord [Minecraft 닉네임] [트랙 이름] [기록] [탑승 카트] [엔진] [영상]

기록을 신청합니다.
이 명령어는 모든 유저가 사용할 수 있으며, 양식에 맞게 제출하면 uiddata 딕셔너리에 입력한 데이터가 저장되고 , 기록 등록 신청 전용 채널에 그 데이터들이 전송됩니다.

+ /showranking [트랙 이름] [엔진] [모드]

## 봇 실행 전 준비
1. 파이썬 버전 확인
- 파이썬 버전 : 3.13

2. 구글 스프레드시트 생성
- 카트라이더: 마인크래프트에 있는 모든 트랙을 시트로 생성
- 기록 등록 신청 데이터 임시 저장 시트 생성 (이름은 RecordApplicationData로 하는 것을 추천)
- 위 시트들 외 다른 시트를 생성할 시, 트랙 시트가 아닌 경우 REACT_NOTTRACK_SHEET 리스트에 포함 시키기 (.env - REACT_NOTTRACK_SHEET)

3. 구글 클라우드 서비스 계정 가입 및 디스코드 봇 생성

### 구글 클라우드 서비스 계정
- 스프레드시트와 파이썬 연동 목적 (서비스 키는 JSON으로 받기)

### 디스코드 봇
- OAuth2 - bot 활성화
- Bot - Privileged Gateway Intents - 모든 항목 활성화
- Bot - Bot Permissions - Administrator 활성화

4. .env 작성
- .env.example을 토대로 작성

5. 의존성 설치  
   ```bash
   pip install -r requirements.txt
   # 또는
   pip3 install -r requirements.txt

6. 리로드 / 글로벌 명령어 반영
아래 명령어 실행:
`/ㄹㄹㄷ` `/ㅅㅋ`

:warning: 반영되기까지 최대 1시간 정도 소요.
디스코드를 껐다 켜면 즉시 반영
