require.config({
  urlArgs: 'bust=' + cacheBuster,
  baseUrl: '/static/js',
  waitSeconds: 30,
  paths: {
    'jquery': 'vendor/jquery',
    'backbone': 'vendor/backbone',
    'underscore': 'vendor/underscore',
    'moment': 'vendor/moment',
    'moment-timezone': 'vendor/moment-timezone-with-data',
    'bootstrap': 'vendor/bootstrap',
    'bootstrap-switch': 'vendor/bootstrap-switch',

    'auth': 'auth',
    'ajax-interceptor': 'ajax-interceptor',
    'fetch-interceptor': 'fetch-interceptor',
    'page-manager': 'page-manager',

    'jobs-view': 'views/jobs/jobs-view',
    'executions-view': 'views/executions/executions-view',
    'logs-view': 'views/logs/logs-view',
    'users-view': 'views/users/list',
    'categories-view': 'views/categories/list',

    'jobs-collection': 'models/jobs',
    'executions-collection': 'models/executions',
    'logs-collection': 'models/logs'
  },

  shim: {
    'backbone': {
      deps: ['underscore', 'jquery'],
      exports: 'Backbone'
    },
    'moment-timezone': {
      deps: ['moment']
    },
    'bootstrap': {
      deps: ['jquery']
    },
    'bootstrap-switch': {
      deps: ['jquery', 'bootstrap']
    }
  }
});

require([
  'jobs-view',
  'executions-view',
  'logs-view',
  'users-view',
  'categories-view',
  'jobs-collection',
  'executions-collection',
  'logs-collection',
  'page-manager',
  'ajax-interceptor',
  'fetch-interceptor',
  'auth',
  'backbone',
  'moment'], function (
    JobsView,
    ExecutionsView,
    LogsView,
    UsersView,
    CategoriesView,
    JobsCollection,
    ExecutionsCollection,
    LogsCollection,
    pageManager,
    ajaxInterceptor,
    fetchInterceptor,
    auth,
    Backbone,
    moment) {
  'use strict';

  // 確保頁面加載完成後才初始化
  $(document).ready(function () {
    // console.log("DOM ready, initializing application...");

    // 主動檢查用戶是否登入
    if (window.location.pathname !== '/login') {
      // console.log("檢查用戶身份驗證狀態...");

      // 從 cookie 中獲取 token
      var token = auth.getCookie('token');

      if (!token) {
        // console.log("未找到 token，重定向到登錄頁面");
        window.location.href = '/login';
        return;
      }

      // 向服務器驗證 token 有效性
      $.ajax({
        url: '/api/v1/auth/verify',
        method: 'GET',
        success: function (response) {
          // console.log("身份驗證成功，繼續加載應用");
          initializeApp();
        },
        error: function (xhr, status, error) {
          console.error("身份驗證失敗:", status, error);
          if (xhr.status === 401) {
            // console.log("Token 無效，重定向到登錄頁面");
            auth.deleteCookie('token');
            window.location.href = '/login';
          }
        }
      });
    } else {
      // console.log("當前在登錄頁面，跳過身份驗證檢查");
    }
  });

  // 應用初始化函數
  function initializeApp() {
    // 確保 bootstrap-switch 已加載
    if (typeof $.fn.bootstrapSwitch === 'undefined') {
      console.error('bootstrap-switch not loaded properly');
    } else {
      // console.log('bootstrap-switch loaded successfully');
    }

    var jobsCollection = new JobsCollection();
    var executionsCollection = new ExecutionsCollection();
    var logsCollection = new LogsCollection();

    new JobsView({
      collection: jobsCollection
    });

    new ExecutionsView({
      collection: executionsCollection
    });

    new LogsView({
      collection: logsCollection
    });

    var usersView = new UsersView();
    var categoriesView = new CategoriesView();

    // 初始化頁面管理
    pageManager.init();

    //
    // Initialize URL router
    //
    var AppRouter = Backbone.Router.extend({
      routes: {
        'jobs': 'jobsRoute',
        'executions': 'executionsRoute',
        'jobs/:jid': 'jobsRoute',
        'executions/:eid': 'executionsRoute',
        'logs': 'logsRoute',
        'users': 'usersRoute',
        'categories': 'categoriesRoute',
        '*actions': 'defaultRoute'
      }
    });

    var switchTab = function (switchTo) {
      var pages = ['jobs', 'executions', 'logs', 'users', 'categories'];
      _.each(pages, function (page) {
        $('#' + page + '-page-sidebar').hide();
        $('#' + page + '-page-content').hide();
        $('#' + page + '-tab').removeClass();
      });
      $('#' + switchTo + '-page-sidebar').show();
      $('#' + switchTo + '-page-content').show();
      $('#' + switchTo + '-tab').addClass('active');
    };

    var appRouter = new AppRouter;
    appRouter.on('route:jobsRoute', function (jobId) {
      switchTab('jobs');
      if (jobId) {
        jobsCollection.getJob(jobId);
      } else {
        jobsCollection.getJobs();
      }
    });

    appRouter.on('route:executionsRoute', function (executionId) {
      switchTab('executions');

      if (executionId) {
        executionsCollection.getExecution(executionId);
      } else {
        // 使用目前選擇的時間範圍
        var range = parseInt($('#filter-time-range').val(), 10);
        var end = moment();
        var start = moment().subtract(range, 'second');
        executionsCollection.getExecutionsByRange(start.toISOString(), end.toISOString());
      }
    });

    appRouter.on('route:logsRoute', function () {
      switchTab('logs');
      // 使用目前選擇的時間範圍
      var range = parseInt($('#logs-filter-time-range').val(), 10);
      var end = moment();
      var start = moment().subtract(range, 'second');
      logsCollection.getLogsByRange(start.toISOString(), end.toISOString());
    });

    appRouter.on('route:usersRoute', function () {
      // 檢查用戶是否為管理員
      if (!window.isAdmin) {
        alert('您沒有權限訪問此頁面');
        appRouter.navigate('jobs', { trigger: true });
        return;
      }
      switchTab('users');
    });

    appRouter.on('route:categoriesRoute', function () {
      // 檢查用戶是否為管理員
      if (!window.isAdmin) {
        alert('您沒有權限訪問此頁面');
        appRouter.navigate('jobs', { trigger: true });
        return;
      }
      switchTab('categories');
    });

    appRouter.on('route:defaultRoute', function (actions) {
      // Anything else defaults to jobs view
      switchTab('jobs');
      jobsCollection.getJobs();
    });

    Backbone.history.start();
  }
});
