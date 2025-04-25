/**
 * Fetch API 攔截器
 * 用於攔截和處理所有 fetch 請求，特別是處理 401 錯誤時自動跳轉到登錄頁面
 */

define(['auth'], function (auth) {
    'use strict';

    console.log('初始化 Fetch 攔截器');

    // 保存原始的 fetch 函數
    var originalFetch = window.fetch;

    // 替換全局的 fetch 函數
    window.fetch = function (input, init) {
        // 在請求前添加一些額外的處理
        console.log('攔截到 fetch 請求:', input);

        // 確保 init 物件存在
        init = init || {};

        // 調用原始的 fetch
        return originalFetch(input, init)
            .then(function (response) {
                // 檢查回應狀態
                console.log('收到 fetch 回應，狀態碼:', response.status);

                if (response.status === 401) {
                    console.log('Fetch 請求收到 401 未授權回應，正在跳轉到登錄頁面...');

                    // 清除 token
                    auth.deleteCookie('token');

                    // 跳轉到登錄頁面
                    window.location.href = '/login';

                    // 拋出錯誤以中斷後續處理
                    throw new Error('未授權，已重定向到登錄頁面');
                }

                // 返回正常回應
                return response;
            })
            .catch(function (error) {
                // 記錄錯誤
                console.error('Fetch 請求錯誤:', error);

                // 檢查是否是網絡或其他可能表示 401 的錯誤
                if (error.message && error.message.includes('Failed to fetch')) {
                    console.log('網絡錯誤可能表示未授權，檢查狀態...');

                    // 檢查當前頁面狀態，如果可能是未授權導致的，則重定向
                    fetch('/api/v1/auth/verify', { method: 'GET' })
                        .then(function (verifyResponse) {
                            if (verifyResponse.status === 401) {
                                console.log('驗證請求確認未授權，正在跳轉到登錄頁面...');
                                auth.deleteCookie('token');
                                window.location.href = '/login';
                            }
                        })
                        .catch(function () {
                            // 驗證請求失敗，可能是網絡問題，暫不處理
                        });
                }

                // 重新拋出錯誤以便上層處理
                throw error;
            });
    };

    console.log('Fetch 攔截器已初始化完成');

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