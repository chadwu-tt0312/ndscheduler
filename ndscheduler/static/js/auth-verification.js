/**
 * 用戶身份驗證管理
 * 在頁面載入時驗證用戶身份並處理頁面顯示
 */

define(['./auth'], function (auth) {
    'use strict';

    var authVerification = {};

    /**
     * 初始化頁面
     * 在頁面載入時執行驗證邏輯
     */
    authVerification.initialize = function () {
        // console.log('初始化驗證模組');

        // 檢查 cookie 中是否有 token
        var token = auth.getCookie('token');

        // 如果有 token，確保頁面不會閃爍
        if (token) {
            // 先隱藏所有頁面內容
            hidePageContents();

            // 驗證用戶身份
            verifyUserAuthentication();
        } else {
            // console.log('未找到 token，檢查是否在登入頁面');
            // 如果不在登入頁面，重定向到登入頁面
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
    };

    /**
     * 隱藏所有頁面內容，防止閃爍
     */
    function hidePageContents() {
        var pages = [
            'jobs-page-content',
            'executions-page-content',
            'logs-page-content',
            'users-page-content',
            'categories-page-content',
            'jobs-page-sidebar',
            'executions-page-sidebar',
            'logs-page-sidebar'
        ];

        pages.forEach(function (pageId) {
            var element = document.getElementById(pageId);
            if (element) element.style.display = 'none';
        });
    }

    /**
     * 向後端發送請求驗證用戶身份
     */
    function verifyUserAuthentication() {
        fetch('/api/v1/auth/verify', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(function (response) {
                if (!response.ok) {
                    console.warn('驗證失敗：回應狀態碼', response.status);
                    handleAuthenticationFailure();
                } else {
                    // console.log('驗證成功');
                }
            })
            .catch(function (error) {
                console.error('驗證請求發生錯誤:', error);
                handleAuthenticationFailure();
            });
    }

    /**
     * 處理身份驗證失敗的情況
     */
    function handleAuthenticationFailure() {
        // 清除 cookie
        auth.deleteCookie('token');

        // 重定向到登入頁面
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
    }

    // 自動初始化
    document.addEventListener('DOMContentLoaded', authVerification.initialize);

    return authVerification;
}); 