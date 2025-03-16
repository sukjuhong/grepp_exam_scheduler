# BE 개발자 과제

시험 일정 예약 시스템 API 개발

## 기술 스택

- `Django`와 `Django REST framework`로 구현되었습니다.
- 인증을 위해 `djangosimplejwt`를 사용했습니다.
- API 문서화를 위해 `drf-spectacular`를 사용했습니다.

## 구현 고려 사항

> [!TIP]
> 요구 사항 중 애매했던 부분이나 없던 부분을 정책적으로 결정한 내용을 서술합니다.

- 고객의 생성 및 수정, 삭제는 관리자만이 가능합니다. (비밀번호 변경 또한 관리자를 통해 이뤄집니다.)
- 고객은 예상치 못한 오류 상황을 대비하기 위해 그렙의 대응 가능 시간인 09:00 ~ 18:00에만 예약이 가능합니다.
- 고객은 당일로부터 3일 뒤부터 15일 뒤까지 예약이 가능합니다. 이는 예약을 변경할 때도 동일하게 적용됩니다.
- 고객은 1시간 단위로 예약이 가능하며, 하루 내에서 시간 제약 없이 가능합니다. (09:00 ~ 18:00도 가능합니다.)
- 고객은 날짜 별로 시간 당 남은 인원을 알 수 있습니다.

## 프로젝트 설정 및 실행 방법

### 개발 환경 설정 (VS Code Devcontainer 사용)

이 프로젝트는 **VS Code의 Devcontainer** 기능을 사용하여 설정할 수 있습니다.

> [!TIP]
> 사전 요구사항
> - [Visual Studio Code](https://code.visualstudio.com/) 설치  
> - [Dev Containers 확장](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) 설치  
> - Docker 설치 및 실행 ([설치 가이드](https://docs.docker.com/get-docker/))

### 실행 방법

1. **이 저장소를 클론합니다.**  

```sh
git clone https://github.com/sukjuhong/grepp_example_scheduler.git
cd grepp_example_scheduler
```

2. VS Code에서 프로젝트를 엽니다.

```sh
code .
```

3. Devcontainer로 재열기

`F1` (또는 `Ctrl + Shift + P`)를 눌러 Command Palette를 엽니다.

`Dev Containers: Rebuild Container` 를 선택합니다.

이때, 개발 환경에 맞는 .env 생성 및 한 개의 슈퍼유저와 두 개의 테스트 고객 계정이 생성됩니다.
슈퍼유저는 `company_name=grepp, password=grepp123`이며,
두개의 테스트 고객은 `company_name=programmers, passowrd=programmers123`, `company_name=monito, password=monito123`입니다.

4. Django 실행하기

```sh
python ./manage.py runserver
```

혹은, 아래의 명령어로 서버를 테스트할 수 있습니다.

```sh
python ./manage.py test
```
