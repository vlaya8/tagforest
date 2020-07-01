var notification_menu_app = new Vue({
  delimiters: ['[[', ']]'],
  el: '#notification_menu_app',
  data () {
    return {
    	showMenu: false,
    }
  },
  methods:{
    toggle: function () {
    	this.showMenu = !this.showMenu
    },
    hide: function () {
    	this.showMenu = false
    },
    onClose () {
      this.showMenu = false
    }
  },
});
