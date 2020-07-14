const fullEntryTitles = JSON.parse(JSON.parse(document.getElementById('entryTitles').textContent));

/*
 * Source: https://stackoverflow.com/questions/118241/calculate-text-width-with-javascript/21015393#21015393
 */

const getTextWidth = (text) => {
  var canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement("canvas"));
  var context = canvas.getContext("2d");
  context.font = "bold 130% Nimbus Sans";
  var metrics = context.measureText(text);
  return metrics.width;
}


/*
 * s: the string to wrap and do ellipsis on
 * maxWidth: the max width before wrapping, in rem
 * maxLine: the maximum amount of lines before ellipsis is done
 */

const ellipsisAndWrap = (s, maxWidth, maxLines) => {
  var ret = '', currentLine = 1, ellipsis = false;
  // Multiply maxwidth by an empiric ratio since getTextWidth doesn't
  // seem to be giving the real width
  maxWidth = maxWidth * 190 / 17;
  while(getTextWidth(s) > maxWidth) {
    var prevWhitespace = -1;
    var currentWidth = 0;

    if(currentLine >= maxLines) {
      if(s.length > 0) {
        ellipsis = true;
        currentWidth += getTextWidth("...");
      }
    }

    for(i = 0; ; i++) {

      // If their is a whitespace, wrap
      if(s.charAt(i) == ' ')
        prevWhitespace = i;

      // This shouldn't happen...
      if( (i+1) > s.length ) {
        break;
      }

      currentWidth += getTextWidth(s.charAt(i))

      if( currentWidth > maxWidth ) {

        if(ellipsis) {
          s = s.slice(0, i) + "...";
          return ret + s;
        }

        // In case of a very long word
        if(prevWhitespace == -1) {
          ret += [s.slice(0, i-1), "-<br/>"].join('');
          s = s.slice(i);
        }

        ret += [s.slice(0, prevWhitespace), "<br/>"].join('');
        s = s.slice(prevWhitespace + 1);
        found = true;
        break;
      }
    }

    currentLine++;
  }

  return ret + s;
}

var entry_list_app = new Vue({
  delimiters: ['[[', ']]'],
  el: '#entry_list_app',
  data: {
    entryDisplayShare,
    selectMode: false,
    selectedEntriesIds: {},
    quickAdd: "None",
  },

  computed: {
    computedSelectedEntries(entryId) {
      return this.selectedEntriesIds[entryId];
    }
  },
  watch: {
    computedSelectedEntries(entryId) {
      
    }
  },

  methods: {
    entryTitle: function(key) {
      if(entryDisplayShare.entryDisplay == "LST") {
        return ellipsisAndWrap(fullEntryTitles[key], 60, 1);
      }
      else if(entryDisplayShare.entryDisplay == "CPS") {
        return ellipsisAndWrap(fullEntryTitles[key], 13, 1);
      }
      else if(entryDisplayShare.entryDisplay == "CPM") {
        return ellipsisAndWrap(fullEntryTitles[key], 15, 2);
      }
      else if(entryDisplayShare.entryDisplay == "CPL") {
        return ellipsisAndWrap(fullEntryTitles[key], 19, 3);
      }
    },

    toggleSelectMode: function() {
      this.selectMode = !this.selectMode;
    },

    removeClass: function() {
      var baseClass = "buttonLink";
      var enableClass = "";
      if(!this.selectMode)
	enableClass = "disabledLink";
      return baseClass + " " + enableClass;
    },

    toggleEntry: function(entryId) {
      this.selectedEntriesIds[entryId] = !this.selectedEntriesIds[entryId];
      this.$forceUpdate();
    },

    entryClass: function(entryId) {

      var baseClass = "buttonLink";
      var selectedClass = "";
      if(entryId in this.selectedEntriesIds) {
	if(this.selectedEntriesIds[entryId])
	  selectedClass = "selectedLink";
      }
      return baseClass + " " + selectedClass;
    },

    getSelectedEntriesIds: function() {
      var idsList = [];
      for(var entryId in this.selectedEntriesIds) {
	if(this.selectedEntriesIds[entryId])
	  idsList.push(entryId);
      }

      return idsList.join(";");

    },

    displayQuickAdd: function(position) {
      return (this.quickAdd == position);
    },

    toggleQuickAdd: function(position) {
      if(this.quickAdd == "None") {
	this.quickAdd = position;
      }
      else {
	this.quickAdd = "None";
      }
    }
  }
});
