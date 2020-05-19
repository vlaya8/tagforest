
const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);

var selected_tags = urlParams.get('selected_tags')

if (selected_tags === null) {
  selected_tags = []
}
else {
  selected_tags = selected_tags.split(",")
}

var tag_select_app = new Vue({
  delimiters: ['[[', ']]'],
  el: '#tag_select_app',
  data: {
    message: 'Hello !',
    selected_tags: selected_tags
  },
  methods: {
    getTagBlockClass: function(primary_class, name) {
      if(this.selected_tags.indexOf(name) >= 0) {
        return primary_class + ' selected'
      }
      else {
        return primary_class
      }
    }
  }
});
