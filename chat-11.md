## q-1

Audit Logs 裡面 Description 呈現內容。但是 pub_args 在這次修改並無變更，只有 minute 變更。要如何修正?
diff: old val => new val
pub_args: ('first parameter', {'second parameter': 'can be a dict'}) => ['first parameter', {'second parameter': 'can be a dict'}]
minute: */1 => */10

---

## answer-1

2025-04-10_05-17-audit-logs-change-display-issue.md

---

## q-2

哪裡有用到 format_job_dict_diff() ?
實際的比較邏輯在哪個 function 之中?

---

## q-3 (反覆3次改不了)

Executions & Audit Logs 頁面顯示切換時預設都只會顯示 10 minutes 的資料。即使畫面上選擇的是 12 hours 。需要手動按 Refresh 才會正確更新資料。要如何改善?

---

## q-4

登入頁面目前使用的是 ADMIN_USER 。
- 如何添加資料表用來管理所有使用者(包含 ADMIN_USER)
- 如何讓使用者根據不同 category 可以看到不同 jobs/executions/auditlogs
- 如何讓使用者根據權限 (Read=只能看，Add=可以增加/修改 job)
請先規劃好相關功能步驟，再與我討論過後才開始

---

## answer-4

2025-04-15_00-35-使用者管理系統功能規劃.md

---

## q-5

1. UserCategoryMapping 表格，與 UserPermissions 表格各有何作用? 
2. 如果只想保留 Users 表格 & UserCategories 表格。要如何調整資料表定義?
3. 使用者資料管理介面和 Category 管理介面可以掛在 "Info" 功能列表之下
4. 不需要更細緻的權限控制
5. Category 的層級只有一層
6. 不需要使用者群組
7. 為何需要資料遷移? 新建資料表與現有資料表有哪些需要變更嗎?

---

## q-6

介面規劃中
- 只需要增加"使用者列表"和"Category 列表"
- is_admin=true 的使用者才可以看到"使用者列表"和"Category 列表"
- 並且列表頁面中有新增/編輯功能

---

## q-7

---

## answer-7

---

## q-9

---

## answer-9

---

## q-9

---

## answer-9
