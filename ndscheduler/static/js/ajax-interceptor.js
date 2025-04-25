/**
 * AJAX 請求攔截器
 * 用於處理 API 請求的全局錯誤，特別是 401 錯誤時自動跳轉到登錄頁面
 */

define(['jquery', 'auth'], function ($, auth) {
    'use strict';

    console.log('初始化 AJAX 攔截器');

    // 設置全局 AJAX 設置
    $.ajaxSetup({
        statusCode: {
            401: function () {
                console.log('收到 401 未授權回應，正在跳轉到登錄頁面...');

                // 清除 token
                auth.deleteCookie('token');

                // 跳轉到登錄頁面
                window.location.href = '/login';
                return false; // 阻止後續處理
            },
            500: function () {
                console.log('收到 500 伺服器錯誤，可能是資料庫連接問題，嘗試驗證身份...');

                // 嘗試進行一次身份驗證檢查
                $.ajax({
                    url: '/api/v1/auth/verify',
                    method: 'GET',
                    success: function (response) {
                        console.log('驗證成功，原始 500 錯誤可能與身份驗證無關');
                    },
                    error: function (xhr) {
                        if (xhr.status === 401) {
                            console.log('驗證失敗，重定向到登錄頁面');
                            // 清除 token
                            auth.deleteCookie('token');
                            // 跳轉到登錄頁面
                            window.location.href = '/login';
                        }
                    }
                });
            }
        },
        // 全局錯誤處理
        error: function (xhr, textStatus, errorThrown) {
            console.log('AJAX 錯誤: ' + textStatus + ', 狀態碼: ' + xhr.status);

            // 如果是 401 錯誤，重新導向到登入頁面
            if (xhr.status === 401) {
                console.log('通過全局錯誤處理捕獲 401 錯誤');

                // 清除 token
                auth.deleteCookie('token');

                // 跳轉到登錄頁面
                window.location.href = '/login';
                return false; // 阻止後續處理
            }

            // 如果是 500 錯誤，檢查是否為資料庫連接問題
            if (xhr.status === 500 && xhr.responseText && xhr.responseText.includes("TimeoutError")) {
                console.log('伺服器資料庫連接問題，可能需要重新登入');

                // 嘗試驗證身份
                $.ajax({
                    url: '/api/v1/auth/verify',
                    method: 'GET',
                    success: function (response) {
                        console.log('身份驗證成功，不需要重新登入');
                    },
                    error: function (xhr) {
                        if (xhr.status === 401) {
                            console.log('身份驗證失敗，重定向到登錄頁面');
                            auth.deleteCookie('token');
                            window.location.href = '/login';
                        }
                    }
                });
            }
        }
    });

    // 添加全局 AJAX 事件處理
    $(document).ajaxError(function (event, jqXHR, ajaxSettings, thrownError) {
        console.log('全局 AJAX 錯誤事件: ' + thrownError + ', 狀態碼: ' + jqXHR.status);

        // 再次檢查 401 錯誤，以防其他攔截點沒有捕獲
        if (jqXHR.status === 401) {
            console.log('全局 AJAX 錯誤事件捕獲 401 錯誤');

            // 清除 token
            auth.deleteCookie('token');

            // 跳轉到登錄頁面
            window.location.href = '/login';
            return false; // 阻止後續處理
        }

        // 檢查 500 錯誤
        if (jqXHR.status === 500) {
            console.log('全局 AJAX 錯誤事件捕獲 500 錯誤');

            // 檢查回應文本是否包含資料庫連接錯誤關鍵字
            if (jqXHR.responseText &&
                (jqXHR.responseText.includes("TimeoutError") ||
                    jqXHR.responseText.includes("connection") ||
                    jqXHR.responseText.includes("database"))) {
                console.log('檢測到資料庫連接錯誤，可能需要重新登入');

                // 嘗試驗證身份
                $.ajax({
                    url: '/api/v1/auth/verify',
                    method: 'GET',
                    success: function (response) {
                        console.log('身份驗證成功，不需要重新登入');
                    },
                    error: function (xhr) {
                        console.log('驗證請求結果：', xhr.status);
                        if (xhr.status === 401) {
                            console.log('身份驗證失敗，重定向到登錄頁面');
                            auth.deleteCookie('token');
                            window.location.href = '/login';
                        }
                    }
                });
            }
        }
    });

    console.log('AJAX 攔截器已初始化完成');

    // 返回攔截器對象
    return {
        // 提供一個顯式的重定向方法，可以在需要時從其他地方調用
        redirectToLogin: function () {
            console.log('手動調用重定向到登錄頁面');
            auth.deleteCookie('token');
            window.location.href = '/login';
        }
    };
}); 