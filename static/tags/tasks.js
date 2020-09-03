var tasks_app = new Vue({
  delimiters: ['[[', ']]'],
  el: '#tasks_app',
  data: {
    currentEdit: 0,
    editMode: false,
    addMode: false,
  },
  methods: {
    editTask: function(taskId) {
      return (this.currentEdit == taskId) && this.editMode;
    },
    enterEditMode: function(taskId) {
      this.currentEdit = taskId;
      this.editMode = true;
    },
    exitEditMode: function() {
      this.editMode = false;
    },
  }
});
