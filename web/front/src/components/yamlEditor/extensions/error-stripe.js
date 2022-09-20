/* eslint-disable no-param-reassign */
/* eslint-disable no-restricted-syntax */
import {
  EditorView,
  Decoration,
  ViewPlugin,
  DecorationSet,
} from '@codemirror/view';
import { RangeSetBuilder } from '@codemirror/rangeset';

const baseTheme = EditorView.baseTheme({
  '.cm-errorStripe': { backgroundColor: '#ff390040 !important' },
});

const stripe = Decoration.line({
  attributes: { class: 'cm-errorStripe' },
});

function stripeDeco(view, position) {
  const line = view.state.doc.lineAt(position);
  const builder = new RangeSetBuilder();
  if (position) {
    builder.add(line.from, line.from, stripe);
  }
  return builder.finish();
}

const showStripes = (getErrorPos) =>
  ViewPlugin.fromClass(
    class {
      decorations = Decoration.set;

      constructor(view) {
        this.decorations = stripeDeco(view, 0);
      }

      update(update) {
        if (update.docChanged || update.viewportChanged) {
          const { position } = getErrorPos(update.state.doc.toString());
          if (!position) {
            this.decorations = stripeDeco(update.view, 0);
            return;
          }
          this.decorations = stripeDeco(update.view, position);
        }
      }
    },
    {
      decorations: (v) => v.decorations,
    },
  );

export function errorStripe(getErrorPos = () => ({})) {
  return [baseTheme, showStripes(getErrorPos)];
}
