const treeIds = JSON.parse(document.getElementById('treeIds').textContent);
const nbTrees = JSON.parse(document.getElementById('nbTrees').textContent);
const initialEntryDisplay = JSON.parse(document.getElementById('initialEntryDisplay').textContent);
const entryDisplayChoices = JSON.parse(document.getElementById('entryDisplayChoices').textContent);

const entryDisplayShare = {
  entryDisplay:null
};

var tree_bar_app = new Vue({
  delimiters: ['[[', ']]'],
  el: '#tree_bar_app',
  data: {
    treeParamDropdown: false,
    treeParam: false,
    addMode: false,
    editMode: false,
    viewMode: true,
    treeBarData: {},
    editTree: {},
    entryDisplayChoices: {},
    entryDisplayShare,
  },
  beforeMount: function() {
    var entryDisplayData;

    for(i = 0; i < nbTrees; i++) {
      Vue.set(this.editTree, treeIds[i], false);
    }

    this.entryDisplayShare.entryDisplay = initialEntryDisplay;

    this.entryDisplayChoices = entryDisplayChoices;
  },
  mounted() {
    if (sessionStorage.entryDisplay) {
      this.entryDisplayShare.entryDisplay = sessionStorage.entryDisplay
    }
  },
  watch: {
    entryDisplayShare: {
      handler: function (entryDisplayShare, newEntryDisplayShare) {
                sessionStorage.entryDisplay = newEntryDisplayShare.entryDisplay;
              },
      deep: true
    }
  },
  methods: {

    toggleTreeParamDropdown: function () {
    	this.treeParamDropdown = !this.treeParamDropdown
    },
    showTreeParam: function () {
    	this.treeParam = true
    },
    hideTreeParam: function () {
    	this.treeParam = false
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
      for(i = 0; i < nbTrees; i++) {
	Vue.set(this.editTree, treeIds[i], false);
      }
      Vue.set(this.editTree, tree_id, true);
    },
    exitEditTree: function(tree_id) {
      Vue.set(this.editTree, tree_id, false);
    }

  }
});
