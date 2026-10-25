# JeSU大阪 府内イベント予定 週次更新
実行機: 豊中Mac mini / job: jesu-osaka-events-weekly / 毎週月曜日09:00 JST。
2026-10-21の社長の範囲提示後の直接承認により、カレンダー欄に限り公式調査・更新・検証・テスト公開・照合・本番公開・照合まで各回確認なしで行う。Drive INDEXの限定追補（fileId 1Y04BGoHtscfwE9bO3q3zN3Rv80PLPAMK）を先に確認する。

1. /Users/yukuno/.local/share/jesu-osaka/repo/docs/event-listing-guidelines.md と content/event-policy.json を読む。今回の時刻はJSTで計算する。
2. python3 /Users/yukuno/.local/share/jesu-osaka/repo/scripts/prepare-weekly.py を実行し、返されたworktreeとoutputだけを編集先にする。現在作業中の元repoを書き換えない。既に同日成果物が検証済みならID・ハッシュの読戻しをし、重複作成しない。
3. 最初にPACkage関連の全件確認を行う。PACkage公式のevents/archive/brands、PACFES/PACLAN/PAC CUP、ゲームパビリオンjpのmeetupと本開催、OsakaPNGとPACsの公開告知、公開可能な案件台帳を照合する。大阪府内の主催・共催・企画運営・運営協力・出演は規模・ジャンル不問でcategory=corporate（表示名「企業主催」）へ。日時が異なる日は別枠にし、JeSU自社開催予定との重複を避ける。内部の未公表案件は候補台帳に保持し公開しない。一般枠では対戦・観戦・実際のゲームプレイ参加を主目的とするものを掲載する。展示・映像・ライド主体の催事をゲーム原作という理由だけで含めない。activity_typeと根拠を記録する。現在のブラウズ／MCP Web検索の機能を確認し、今後180日の大阪府内の主要イベントを公式発表から調査する。既存掲載の公式URLを全件開き、日付・会場・主催・中止／延期・申込先を確認する。JeSU、メーカー（KONAMI、CAPCOM、SEGA、Nintendo、Riot等）、主要プロチーム（REJECT、ZETA DIVISION、Crazy Raccoon等）、配信者本人／運営の公式サイト、府の大規模大会支援情報を探索元とする。見つからない種別を埋めるための架空掲載をしない。
4. PACkage関連は公式な関係根拠と当該日程、一般枠は主催者と公式URL・府内会場・大型根拠が揃ったものだけをcontent/osaka-events.jsonに入れる。公式ドメインが新規なら運営関係を確認してpolicyのsource_hostsへ追加し、根拠を週次記録へ。source_hosts追加だけで掲載可にはしない。日時が実際に確認できたイベントだけchecked_atを更新。取得不能は終了・中止と推測せず保持。前回と変わらなくても実際に全件再確認できた場合だけlast_checkedを当日に更新する。
5. 新規・変更・終了・見送り・取得不能をoutputの隣のresearch.jsonに記録（URL・観測日時・判定理由・担当のみ、記事本文転載や個人データ不要）。オンライン限定と府外は除外。行政支援対象は公式大会サイトと府の支援ページを両方確認。媒体のまとめだけを根拠にしない。
6. worktreeで python3 scripts/render-events.py、python3 -m unittest discover -s tests -p test_event_policy.py、node --test test/*.test.cjs を実行。その後 python3 scripts/build.py --preview --output <output>/preview、python3 scripts/validate.py <output>/preview --preview、python3 scripts/export-review.py <output>/preview <output>/offline を実行。report本文と写真は変更しない。ローカルGitコミットは可、fetchが必要ならread-onlyの公式gh／gitで確認し、公開は下記の限定承認とweekly-release.pyを通す場合に限る。
7. outputにreview.zip（preview、offline、research.json、JSON差分、検証記録、元コミットSHA）と確認用index.htmlを保存。更新結果をverification.jsonへ、sha256・日程数・確認成功数・失敗数・公開未実施・次回トリガーを記録する。
8. 既存共有Driveフォルダ 1OKVDoYaF5417mJbZvH-ReJNpX5_l2kjW へ日付入り「JeSU大阪_府内イベント週次確認_YYYYMMDD.zip」と同名HTMLを新規保存。元の手動確認版ファイルIDは上書きしない。保存後にコネクタで再取得して元ファイルSHA256と一致を確認。クラウド保存不能ならローカルを保持し未検証として記録し、成功と書かない。
9. Notion作業ログ 3ff0f7d0-c7b1-8162-969f-c4eeb648e9df をfetchして週次結果とDrive ID・SHA・次回・実際の公開結果または停止理由を追記する。社長の承認列や完了を自分で設定しない。社外・Discordへの送信はしない。結果はこのCLI実行の回答とNotionログへ返す。
10. 機械検証、クラウド読戻し、自然起動を分けて記録。今回がmanual_or_unverifiedなら手動試験と明記し、将来の週次処理キーを先取りしない。署名値・個人情報・生会話は記録しない。失敗時は元repoと正常データを維持する。

表示上の追記（社長の直接修正）: イベントカードにPACkageの役割行（企画・運営に参画等）は表示しない。概要文にも役割を繰り返さない。カテゴリ・正式な主催者は維持し、掲載判定に必要なpackage_relationの根拠は内部データに保持する。

カレンダー表示: 当月を初期表示し、予定一覧はJeSU本部・JeSU大阪が主催・共催・運営・後援・協力するイベントだけを対象に、閲覧時の日本時間の当日を含む直近最大2件を日付・開始時刻順で表示する。関与の判定はSNS用と同じく、category=jesuかつ主催者がJeSU、または公式記載に基づくjesu_role（主催・共催・運営・後援・協力）を使う。PACkageの関与だけでは対象にせず、対象が1件・0件ならその件数のままにする。同じ複数日イベントは1件として数え、終了済み・中止・延期は初期の直近2件へ含めない。全月・月別の一覧は利用者が明示的に選んだ場合だけ展開する。月別ボタンと日付から詳細へ進む動作を維持し、週次生成で初期表示を全件へ戻さない。12月以降・翌年の公式発表も調査し、空の月は未発表の予定を補わない。JeSU自社開催は同じデータをカレンダーに反映し、detail_anchorで上の開催案内へリンクする（詳細カードの重複作成はしない）。JeSU公式勉強会のseminarは一般競技のactivity_type制限の例外。毎週、本文側の開催案内と日程・会場・申込先の一致も確認する。

カレンダー紹介文は「大阪で出会える、ゲームとeスポーツの大きな舞台。」「JeSU関連、ゲームメーカー、プロチーム・配信者の主要イベントやフォームからご登録いただいたイベント等を公式発表からご紹介します。」とする。PACkageの関係区分・全件掲載の説明段落は表示しない。末尾の外部主催者・公式サイト確認の案内は維持。掲載判定やイベントデータの基準は変更しない（社長の文言差し替え指示）。

掲載漏れ防止: 検索エンジンの結果・旧記事・カレンダーの空表示だけで不存在と判定しない。PACkage公式Xの最新告知、公式Peatixグループの公開予定、既存案件台帳の開催月を突合し、候補ごとに会場の公式トップ→現在のイベント詳細へ進む。スパワールドは公式ハロウィン等の季節ページ内のゲーム体験枠も読む。サイト内の無関係なリンクや改変が疑われる内容は根拠にせず、当該イベント本文と会社公式告知で照合。定期イベントの過去年日付を流用しない。PACkage関係根拠は会社公式ドメインか確認済み公式X PACkage_2018 の固定ポストURLを用いる。他アカウント・検索URL・プロフィールURLだけでは根拠としない。Peatix公開ページの開催時間・料金も確認し、出展料・オプション・ドリンク代と一般入場料を区別する。

## 2026-10-21 週次実装の追記

自然起動の観測がある回だけ通常のprepare-weekly.pyを使い、それ以外はprepare-weekly.py --manualを使う。手動はmanual-日時の別キーとなり、将来の週次キーを消費しない。既存作業場を再利用するときは最初のbase_shaを保持する。

research.jsonには機械検証用にschema_version=1、discovery、sourcesを含める。discoveryはpackage / jesu / publishers / teams_creators / submissionsの5つを実際に探索した場合だけtrue。sourcesは全イベントのevent_id、official_urlと同じurl、status（verifiedまたはunavailable）、observed_at（当日JSTのISO8601）を持つ。将来イベントを削除する場合も旧IDと公式URLの当日の確認根拠が必要。取得不能を成功と書かない。checked_atとlast_checkedは実際に確認できた範囲だけ更新する。

調査後に実行：
python3 /Users/yukuno/.local/share/jesu-osaka/repo/scripts/weekly-release.py stage --worktree <worktree> --research <run>/research.json --output <run>/frozen
python3 /Users/yukuno/.local/share/jesu-osaka/repo/scripts/weekly-release.py publish --candidate <run>/frozen --dry-run

frozenには本番・テスト両成果物とcandidate.json、research.jsonを保存する。確認用offline HTMLとZIPを作り、従来どおりDrive保存・再取得照合する。

公開はdocs/weekly-publication-proposal.mdと現在の正本に従う。2026-10-21に社長の限定承認を正本へ反映し、ゲートはenabled=trueになった。現在の正本とゲートを読み、上記stage/dry-run、Drive保存・再取得照合が成功したらpublish（--dry-runなし）を実行する。カレンダー欄は各回の追加承認待ちにしない。ゲートが無効なら公開せず候補保存まで。自分で正本・ゲート・承認を変更しない。

公開後はpublication.jsonへ実コミットと照合結果を記録する。source_imported=falseなら次回公開を進めず編集元を照合する。publication-started.jsonがある失敗回は自動再送せず、現状を先に確認する。

## SNS制作への受け渡し（2026-10-21 社長直接依頼）

カレンダーの本番公開と全件照合、source_imported=trueを確認した後（変更なしなら本番欄と編集元の一致確認後）、docs/calendar-sns.mdに従い、python3 /Users/yukuno/.local/share/jesu-osaka/repo/scripts/queue-calendar-sns.py --output <run>/sns-intake.json を実行する。既存mascot-editorial/inboxへJeSU大阪X向け事実パックを渡し、同じ週・内容を重複作成しない。SNS受け渡し失敗は本番サイトの正常更新と区別して記録・再開する。未公開候補や合成データは渡さない。SNSは本人の版ごとの承認が必要。受信箱登録を投稿済みと書かない。既存x-weekly-draftsが日次に処理するが、週次実行自身も実際の原稿・未チェックの媒体別承認行への到達を確認し、未処理なら現行人格と公式情報を確認して現行SNSスキルのslot-inventory取得と既存campaign_pipeline prepare-batch --slot-inventory / sheet-prepend経由で登録する。新規の外部送信はしない。

## 主催区分の整理（2026-10-21 社長直接修正）

公開カテゴリ「PACkage関連」は廃止し「企業主催」（category=corporate）に統合する。既存のPACkage関係6件とREDEE主催4件は企業主催へ。REDEEは行政の支援対象であっても主催者を基準に分類し、publicへ戻さない。ゲームメーカー・プロチーム・配信者・JeSUの専用区分は維持。掲載の可否と主催区分を分離し、package_relatedとpackage_relationは内部の従来の掲載条件の検証にだけ使う。企業主催全体へPACkageの小規模・180日超の例外を広げない。

カレンダーの週は日曜始まり（日・月・火・水・木・金・土）。日曜を左端の赤、土曜を右端の青とし、静的HTMLとJavaScriptによる月切替の両方で同じ日付配置を維持する（社長直接指示）。日付ラベルの曜日計算は表示列の並びと混同しない。
