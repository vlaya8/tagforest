var view_notifications_app = new Vue({
  delimiters: ['[[', ']]'],
  el: '#view_notifications_app',
  data () {
    return {
        dialogVisible: false,
        dialogMessage: "",
    }
  },
  methods:{
    showDialog: function (dialog_message) {
    	this.dialogVisible = true
        this.dialogMessage = dialog_message
    },
    hide: function () {
    	this.dialogVisible = false
    },
  },
});
