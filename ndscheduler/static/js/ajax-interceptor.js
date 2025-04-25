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