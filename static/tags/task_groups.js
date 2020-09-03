var task_groups_app = new Vue({
  delimiters: ['[[', ']]'],
  el: '#task_groups_app',
  data: {
    currentEdit: 0,
    editMode: false,
    addMode: false,
  },
  methods: {
    editGroup: function(groupId) {
      return (this.currentEdit == groupId) && this.editMode;
    },
    enterEditMode: function(groupId) {
      this.currentEdit = groupId;
      this.editMode = true;
    },
    exitEditMode: function() {
      this.editMode = false;
    },
  }
});
