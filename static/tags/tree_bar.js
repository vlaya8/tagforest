var tree_bar_app = new Vue({
  delimiters: ['[[', ']]'],
  el: '#tree_bar_app',
  data: {
    addMode: false,
    editMode: false,
    viewMode: true,
    tree_bar_data: {},
    editTree: {},
  },
  methods: {
    beforeMount: function() {
      this.tree_bar_data = JSON.parse(document.getElementsByTagName('body')[0].getAttribute('tree_bar_data') || '{}' );
      for(i = 0; i < this.tree_bar_data['nb_trees']; i++) {
	Vue.set(this.editTree, this.tree_bar_data['tree_ids'][i], false);
      }
    },
    enterAddMode: function() {
      this.addMode = true;
      this.viewMode = false;
    },
    enterEditMode: function() {
      this.editMode = true;
      this.viewMode = false;
    },
    exitAddMode: function() {
      this.addMode = false;
      this.viewMode = true;
    },
    exitEditMode: function() {
      this.editMode = false;
      this.viewMode = true;
    },

    enterEditTree: function(tree_id) {
      for(i = 0; i < this.tree_bar_data['nb_trees']; i++) {
	Vue.set(this.editTree, this.tree_bar_data['tree_ids'][i], false);
      }
      Vue.set(this.editTree, tree_id, true);
    },
    exitEditTree: function(tree_id) {
      Vue.set(this.editTree, tree_id, false);
    }

  }
});
