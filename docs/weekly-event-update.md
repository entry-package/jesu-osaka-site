# JeSU大阪 府内イベント予定 週次更新
実行機: 豊中Mac mini / job: jesu-osaka-events-weekly / 毎週月曜日09:00 JST。
2026-10-20の社長の直接依頼により、公式イベントの週次収集・内部確認版の更新を行う。公開・送信の権限にはしない。

1. /Users/yukuno/.local/share/jesu-osaka/repo/docs/event-listing-guidelines.md と content/event-policy.json を読む。今回の時刻はJSTで計算する。
2. python3 /Users/yukuno/.local/share/jesu-osaka/repo/scripts/prepare-weekly.py を実行し、返されたworktreeとoutputだけを編集先にする。現在作業中の元repoを書き換えない。既に同日成果物が検証済みならID・ハッシュの読戻しをし、重複作成しない。
3. 最初にPACkage関連の全件確認を行う。PACkage公式のevents/archive/brands、PACFES/PACLAN/PAC CUP、ゲームパビリオンjpのmeetupと本開催、OsakaPNGとPACsの公開告知、公開可能な案件台帳を照合する。大阪府内の主催・共催・企画運営・運営協力・出演は規模・ジャンル不問でcategory=packageへ。日時が異なる日は別枠にし、JeSU自社開催予定との重複を避ける。内部の未公表案件は候補台帳に保持し公開しない。一般枠では対戦・観戦・実際のゲームプレイ参加を主目的とするものを掲載する。展示・映像・ライド主体の催事をゲーム原作という理由だけで含めない。activity_typeと根拠を記録する。現在のブラウズ／MCP Web検索の機能を確認し、今後180日の大阪府内の主要イベントを公式発表から調査する。既存掲載の公式URLを全件開き、日付・会場・主催・中止／延期・申込先を確認する。JeSU、メーカー（KONAMI、CAPCOM、SEGA、Nintendo、Riot等）、主要プロチーム（REJECT、ZETA DIVISION、Crazy Raccoon等）、配信者本人／運営の公式サイト、府の大規模大会支援情報を探索元とする。見つからない種別を埋めるための架空掲載をしない。
4. PACkage関連は公式な関係根拠と当該日程、一般枠は主催者と公式URL・府内会場・大型根拠が揃ったものだけをcontent/osaka-events.jsonに入れる。公式ドメインが新規なら運営関係を確認してpolicyのsource_hostsへ追加し、根拠を週次記録へ。source_hosts追加だけで掲載可にはしない。日時が実際に確認できたイベントだけchecked_atを更新。取得不能は終了・中止と推測せず保持。前回と変わらなくても実際に全件再確認できた場合だけlast_checkedを当日に更新する。
5. 新規・変更・終了・見送り・取得不能をoutputの隣のresearch.jsonに記録（URL・観測日時・判定理由・担当のみ、記事本文転載や個人データ不要）。オンライン限定と府外は除外。行政支援対象は公式大会サイトと府の支援ページを両方確認。媒体のまとめだけを根拠にしない。
6. worktreeで python3 scripts/render-events.py、python3 -m unittest discover -s tests -p test_event_policy.py、node --test test/*.test.cjs を実行。その後 python3 scripts/build.py --preview --output <output>/preview、python3 scripts/validate.py <output>/preview --preview、python3 scripts/export-review.py <output>/preview <output>/offline を実行。report本文と写真は変更しない。ローカルGitコミットは可、fetchが必要ならread-onlyの公式gh／gitで確認し、push・PR・マージ・公開はしない。
7. outputにreview.zip（preview、offline、research.json、JSON差分、検証記録、元コミットSHA）と確認用index.htmlを保存。更新結果をverification.jsonへ、sha256・日程数・確認成功数・失敗数・公開未実施・次回トリガーを記録する。
8. 既存共有Driveフォルダ 1OKVDoYaF5417mJbZvH-ReJNpX5_l2kjW へ日付入り「JeSU大阪_府内イベント週次確認_YYYYMMDD.zip」と同名HTMLを新規保存。元の手動確認版ファイルIDは上書きしない。保存後にコネクタで再取得して元ファイルSHA256と一致を確認。クラウド保存不能ならローカルを保持し未検証として記録し、成功と書かない。
9. Notion作業ログ 3ff0f7d0-c7b1-8162-969f-c4eeb648e9df をfetchして週次結果とDrive ID・SHA・次回・公開確認待ちを追記する。社長の承認列や完了を自分で設定しない。社外・Discordへの送信はしない。結果はこのCLI実行の回答とNotionログへ返す。
10. 機械検証、クラウド読戻し、自然起動を分けて記録。今回がmanual_or_unverifiedなら手動試験と明記し、将来の週次処理キーを先取りしない。署名値・個人情報・生会話は記録しない。失敗時は元repoと正常データを維持する。
