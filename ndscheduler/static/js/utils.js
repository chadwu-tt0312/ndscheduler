require.config({
  paths: {
    'spin': 'vendor/spin',
    'noty': 'vendor/jquery.noty',
    'jquery': 'vendor/jquery',
    'moment': 'vendor/moment'
  },

  shim: {
    'noty': {
      deps: ['jquery']
    }
  }
});

define(['spin', 'noty', 'moment', 'jquery'], function (Spinner, noty, moment, $) {
  'use strict';

  /**
   * Starts a spinner.
   *
   * @param {String} parentDomId The parent element id for spinner.
   * @return {Spinner} object of Spinner
   */
  var startSpinner = function (parentDomId) {
    var opts = {
      lines: 13, // The number of lines to draw
      length: 20, // The length of each line
      width: 10, // The line thickness
      radius: 30, // The radius of the inner circle
      corners: 1, // Corner roundness (0..1)
      rotate: 0, // The rotation offset
      direction: 1, // 1: clockwise, -1: counterclockwise
      color: '#000', // #rgb or #rrggbb or array of colors
      speed: 1, // Rounds per second
      trail: 60, // Afterglow percentage
      shadow: false, // Whether to render a shadow
      hwaccel: false, // Whether to use hardware acceleration
      className: 'spinner', // The CSS class to assign to the spinner
      zIndex: 2e9, // The z-index (defaults to 2000000000)
      top: '150%', // Top position relative to parent
      left: '50%'  // Left position relative to parent
    };
    var spinner = new Spinner(opts).spin();
    $('#' + parentDomId).html(spinner.el);
    return spinner;
  };

  /**
   * Stops a spinner.
   *
   * @param {Spinner} spinner The spinner object to stop.
   */
  var stopSpinner = function (spinner) {
    spinner.stop();
  };

  /**
   * Display an error message.
   *
   * @param {String} msg Error message to display.
   */
  var alertError = function (msg) {
    // 檢查是否為權限被拒絕的訊息
    if (msg && (msg.indexOf('Permission denied') !== -1 || msg.indexOf('權限被拒') !== -1)) {
      // 權限被拒絕時，僅在控制台記錄
      console.log('權限錯誤: ' + msg);
      return;
    }

    // 其他錯誤訊息正常顯示
    window.noty({
      type: 'error',
      text: msg,
      timeout: 3000,
      layout: 'top',
      theme: 'defaultTheme',
      maxVisible: 5,
      animation: {
        open: { height: 'toggle' },
        close: { height: 'toggle' },
        easing: 'swing',
        speed: 500
      }
    });
  };

  /**
   * Display a success message.
   *
   * @param {String} msg Success message to display.
   */
  var alertSuccess = function (msg) {
    window.noty({
      type: 'success',
      text: msg,
      timeout: 2000,
      layout: 'top',
      theme: 'defaultTheme',
      maxVisible: 5,
      animation: {
        open: { height: 'toggle' },
        close: { height: 'toggle' },
        easing: 'swing',
        speed: 500
      }
    });
  };

  /**
   * 安全地建立 moment 實例，避免棄用警告
   * 
   * @param {String|Date} date 日期時間字串或物件
   * @param {String} format 格式字串 (可選)
   * @return {moment} moment 實例
   */
  var createMoment = function (date, format) {
    if (!date) {
      return moment(); // 現在時間
    }

    if (format) {
      return moment(date, format); // 指定格式解析
    }

    if (date instanceof Date) {
      return moment(date.getTime()); // 使用時間戳來避免警告
    }

    if (typeof date === 'string') {
      // 嘗試 ISO 8601 格式解析
      if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(date)) {
        return moment(date, moment.ISO_8601);
      }

      // Unix 時間戳 (秒)
      if (/^\d{10}$/.test(date)) {
        return moment.unix(parseInt(date, 10));
      }

      // Unix 時間戳 (毫秒)
      if (/^\d{13}$/.test(date)) {
        return moment(parseInt(date, 10));
      }
    }

    // 若無法確定格式，仍使用一般方式，但至少我們嘗試了避免警告
    return moment(date);
  };

  /**
   * Get json object of arguments of a task.
   *
   * @param {String} argsString Arguments passed to a task in json string.
   * @return {*} json object
   * @private
   */
  var getTaskArgs = function (argsString) {
    // argsString should be a json string
    if (argsString.trim() === '') {
      return [];
    }

    return JSON.parse(argsString);
  };

  /**
   * Get query parameter.
   *
   * @param {String} name query parameter name.
   * @return {String} value of that query parameter.
   */
  var getParameterByName = function (name) {
    var url = window.location.href;
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(url);
    if (!results) {
      return undefined;
    }
    return results[1] || undefined;
  };

  /**
   * Public functions
   */
  return {
    startSpinner: startSpinner,
    stopSpinner: stopSpinner,

    alertSuccess: alertSuccess,
    alertError: alertError,

    createMoment: createMoment,
    getTaskArgs: getTaskArgs,
    getParameterByName: getParameterByName
  };
});
