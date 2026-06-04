# QA_REPORT: v20.4.42 未持倉非可買卡片 attribution 兩層可讀化

## 測試範圍

任務尺寸為 normal_patch、QA L2；本輪驗收限制在 formatter / visible attribution / version / official message-list replay，不擴成 full pytest、production replay、DB 或 live Telegram。

讀取並比對：

- TASK.md
- CHANGELOG.md
- git diff
- core/generator.py
- presentation/report.py
- tests/test_generator_report.py

可吸收 diff：

- CHANGELOG.md
- core/generator.py
- presentation/report.py
- tests/test_generator_report.py

worktree tracked 狀態只有上述 4 檔修改；未看到本輪範圍外 tracked 殘留。QA 只建立 / 使用 .qa_tmp/ 作暫存，未修改 tracked file。

## 風險預算與停止條件

本輪最值得抓的風險：

1. CHANGELOG.md 與實際 diff 再次不一致。
   - 驗證：比對 diff 中 VERSION、formatter、人話化 source、test rename / assertions。
   - 停止條件：若 CHANGELOG 宣稱不存在的檔案、行為或覆蓋層級，直接阻塞。
2. 官方 message-list 手機閱讀仍混淆可買 / 不可買。
   - 驗證：跑 targeted official replay，檢查 summary -> unheld card 順序、非可買兩行、可買與 trend_continuation 不出兩行。
   - 停止條件：若只 helper 通過、official replay 失敗或卡片主結論互相矛盾，阻塞。
3. raw enum / 舊版字串殘留。
   - 驗證：rg 搜 v20.4.41，並用 replay assertion 反證 FAILED_BREAKOUT、LIMIT_LOCK、WEAK_REBOUND、source missing 類 raw wording 不外露。
   - 停止條件：使用者可見 output 或 current-version test expectation 有殘留，阻塞。

## 關聯風險掃描

CHANGELOG.md 與 diff 對齊：有準確列出 core/generator.py 的 VERSION v20.4.42 與 dominant_reject_reasons() source wording 變更；有列出 presentation/report.py 的兩行 attribution、人話化 source、可買 / trend_continuation 不輸出 attribution；有列出 tests/test_generator_report.py 的 v20.4.42 replay rename / assertions 與 version expectation 更新。

實際 diff 未碰策略核心、RR 公式、can_buy / is_valid_entry 判定、持倉狀態機、DB write / read path、live Telegram。core/generator.py 只有版本與 rejected summary wording 變更。

注意：CHANGELOG.md 的自檢命令區仍有一條歷史 command string 帶 v20_4_41 的 -k 名稱與 pycache path；QA 不列 blocker，因為後續同段已列正確 test_v20_4_42...，且實際相關 source / test 檔 rg v20.4.41 無殘留。

## 跨區塊語意一致性

官方 replay 通過後，summary 與未持倉卡片一致：

- RR 不足卡片顯示 卡關主因：RR不足 與 RR 差值。
- 距突破 6% 顯示 需<=4%｜差2%；距突破 2% 負例不列距突破差距。
- 過熱 / Lv.3 / FAILED_BREAKOUT / 盤後待確認 / limit lock / weak rebound 皆優先顯示人話化主因，不混入誤導 RR 或 entry quality 次因。
- 真正可買與 trend_continuation 小倉 BUY 卡片不顯示 卡關主因： / 量化差距：。
- v20.4.42 出現在 official header / summary expectations。

## 使用者誤讀風險

按 Owner 手機閱讀順序檢查：summary 先給新倉是否可行動，未持倉卡片再列主因與量化差距。非可買卡片沒有「建議買入」「可立即買」等像推薦的文案；source missing 路徑仍 fail closed，summary 顯示無有效進場，卡片顯示資料來源缺失，不把缺資料候選放成可買。

## 失敗標本反證

失敗標本是 v20.4.41 盤後非可買卡片只有單行 到達可買差距。本輪 official replay 反證結果：

- 非可買卡片改為兩行 卡關主因：... / 量化差距：...。
- Replay output 不再含 到達可買差距。
- version 升為 v20.4.42。
- post-market ordinary prepare 不是資料不足，而是盤後待確認。

## 質疑與反證

QA 未只重跑 Tech 自檢；補跑 source-missing direct consumer 路徑：

- test_v20_4_10_summary_hides_strongest_when_candidate_source_missing：1 passed。
- 反證 source missing 可買候選不會被 summary 當最強 / 可買，不會在未持倉卡外露 raw Source line。

執行命令結果：

- git diff --check：passed。
- rg 'v20\\.4\\.41' tests/test_generator_report.py core/generator.py presentation/report.py：無匹配。
- targeted L2 pytest：
  - test_v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay
  - test_confirmed_evidence_preserves_limit_lock_chase_hard_blocker
  - test_0604_v20_4_37_generate_mobile_consistency_message_list_replay
  - 結果：3 passed。
- py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed。
- 曾誤跑一條不存在的 pytest -k，結果 169 deselected、exit 5；已更正，不納入通過證據。

## 未測項目

- 未跑 full pytest，符合 normal_patch / L2 範圍控制。
- 未跑 production runner artifact。
- 未讀 production source artifact。
- 未做 DB read/write。
- 未做 live Telegram delivery。
- 未驗證 commit / push gate，這是 Architect 收口責任。

## QA 結論

通過
