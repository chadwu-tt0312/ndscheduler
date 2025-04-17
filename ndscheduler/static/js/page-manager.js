/**
 * 頁面管理功能
 */

define(['jquery', 'auth', 'bootstrap'], function ($, auth) {
    'use strict';

    var pageManager = {};
    var user = auth.verifyUser();

    /**
     * 初始化頁面
     */
    pageManager.init = function () {
        // 確保jQuery和頁面已經準備好
        if (typeof $ === 'undefined') {
            console.error('jQuery not loaded. Cannot initialize page.');
            return;
        }

        console.log('Initializing page manager');

        // 更新網站標題
        pageManager.updateWebsiteTitle();

        // 顯示/隱藏管理員選項
        pageManager.setupAdminOptions();

        // 確保 Bootstrap 下拉選單正常工作
        pageManager.setupDropdowns();

        // 綁定登出按鈕事件
        pageManager.setupLogoutButton();

        // 監聽 hash 變化
        window.addEventListener("hashchange", pageManager.handleHashChange);

        // 初始頁面載入時顯示相應內容
        pageManager.handleHashChange();

        console.log('Page manager initialized successfully');
    };

    /**
     * 更新網站標題
     */
    pageManager.updateWebsiteTitle = function () {
        var websiteTitle = document.getElementById("website-title");
        if (websiteTitle && user.username) {
            var baseTitle = websiteTitle.textContent.split("@")[0];
            websiteTitle.textContent = baseTitle + "@" + user.username;
        }
    };

    /**
     * 設置管理員選項
     */
    pageManager.setupAdminOptions = function () {
        if (user.isAdmin === true) {
            // 顯示管理員選項
            var adminElements = document.getElementsByClassName("admin-only-dropdown");
            Array.from(adminElements).forEach(function (element) {
                if (element) {
                    element.style.display = "block";
                    // 確保樣式不會被覆蓋
                    element.setAttribute("style", "display: block !important");
                }
            });

            // 顯示管理員頁面內容
            var adminPageElements = document.getElementsByClassName("admin-only");
            Array.from(adminPageElements).forEach(function (element) {
                if (element) {
                    // 不直接顯示，僅移除 display:none 樣式
                    element.classList.remove("admin-only");
                }
            });

            console.log("管理員選項已設置");
        } else {
            console.log("非管理員用戶，不顯示管理員選項");
        }
    };

    /**
     * 設置下拉選單
     */
    pageManager.setupDropdowns = function () {
        $(document).ready(function () {
            $(".dropdown-toggle").dropdown();
        });
    };

    /**
     * 設置登出按鈕
     */
    pageManager.setupLogoutButton = function () {
        var logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", function (e) {
                e.preventDefault();
                auth.logout();
            });
        }
    };

    /**
     * 處理 hash 變化
     */
    pageManager.handleHashChange = function () {
        var hash = window.location.hash.substring(1) || "jobs";
        pageManager.showPage(hash);
    };

    /**
     * 顯示指定頁面
     */
    pageManager.showPage = function (pageId) {
        // 處理側邊欄容器
        var sidebarContainer = document.querySelector(".sidebar");
        if (sidebarContainer) {
            sidebarContainer.style.display = ["users", "categories"].includes(pageId) ? "none" : "block";
        }

        // 調整主內容區域的類別
        var mainContent = document.querySelector(".main");
        if (mainContent) {
            if (["users", "categories"].includes(pageId)) {
                mainContent.className = "col-sm-12 col-md-12 main";
            } else {
                mainContent.className = "col-sm-9 col-sm-offset-3 col-md-10 col-md-offset-2 main";
            }
        }

        // 隱藏所有頁面
        var pages = {
            jobs: ["jobs-page-content", "jobs-page-sidebar"],
            executions: ["executions-page-content", "executions-page-sidebar"],
            logs: ["logs-page-content", "logs-page-sidebar"],
            users: ["users-page-content"],
            categories: ["categories-page-content"],
        };

        // 隱藏所有頁面和側邊欄
        Object.values(pages)
            .flat()
            .forEach(function (elementId) {
                var element = document.getElementById(elementId);
                if (element) {
                    element.style.display = "none";
                }
            });

        // 顯示當前頁面
        if (pages[pageId]) {
            pages[pageId].forEach(function (elementId) {
                var element = document.getElementById(elementId);
                if (element) {
                    if ((pageId === "users" || pageId === "categories") && !user.isAdmin) {
                        return;
                    }
                    element.style.display = "block";
                }
            });
        }

        // 更新導航標籤狀態
        document.querySelectorAll(".nav li").forEach(function (tab) {
            tab.classList.remove("active");
        });
        var currentTab = document.getElementById(pageId + "-tab");
        if (currentTab) {
            currentTab.classList.add("active");
        }

        // 更新頁面標題
        var subHeader = document.querySelector(".sub-header");
        if (subHeader) {
            var titles = {
                jobs: "Jobs",
                executions: "Executions",
                logs: "Audit Logs",
                users: "Users",
                categories: "Categories",
            };
            subHeader.textContent = titles[pageId] || pageId;
        }
    };

    return pageManager;
}); 