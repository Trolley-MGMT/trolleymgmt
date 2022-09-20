import React from 'react';
import { StreamLanguage } from '@codemirror/stream-parser';
import { yaml } from '@codemirror/legacy-modes/mode/yaml';
import { EditorView, EditorState, basicSetup } from '@codemirror/basic-setup';
import { keymap, Range, Decoration } from '@codemirror/view';
import { indentWithTab } from '@codemirror/commands';
import { StateField, StateEffect, EditorSelection } from '@codemirror/state';
import { Tooltip, hoverTooltip } from '@codemirror/tooltip';
import { zebraStripes } from './extensions/zebra-stripes';
import { errorStripe } from './extensions/error-stripe';
import { getCurrentWord } from './model';

// Effects can be attached to transactions to communicate with the extension
const addMarks = StateEffect.define();
const filterMarks = StateEffect.define();

const myTheme = EditorView.theme({
  '.cm-activeLine': {
    backgroundColor: '#5973bb2e',
  },
});

// This value must be added to the set of extensions to enable this
const markFieldExtension = StateField.define({
  // Start with an empty set of decorations
  create() {
    return Decoration.none;
  },
  // This is called whenever the editor updates—it computes the new set
  update(prevValue, tr) {
    // Move the decorations to account for document changes
    let newValue = prevValue.map(tr.changes);
    // If this transaction adds or removes decorations, apply those changes
    // eslint-disable-next-line no-restricted-syntax
    for (const effect of tr.effects) {
      if (effect.is(addMarks)) {
        newValue = newValue.update({ add: effect.value, sort: true });
      }
      if (effect.is(filterMarks)) {
        newValue = newValue.update({ filter: effect.value });
      }
    }
    return newValue;
  },
  // Indicate that this field provides a set of decorations
  provide: (f) => EditorView.decorations.from(f),
});

const errorMark = Decoration.mark({
  attributes: {
    style: 'background-color: rgba(255, 0, 0, 0.5)',
  },
});

const YamlInput = React.forwardRef(
  (
    {
      value = '',
      onChange = () => null,
      onSelect = () => null,
      onSetCursor = () => null,
      error,
      options: { theme = undefined, handleTabs = false } = {},
      getErrorPos,
    },
    editorRef,
  ) => {
    const mount = React.useRef(null);
    const view = React.useRef(null);
    const currentValue = React.useRef(value);
    const currentSelection = React.useRef('');
    const currentUnderCursorWord = React.useRef('');

    const actionReplace = ({ text, from, to }) => {
      const toCalc = to || from + text.length;

      view.current.dispatch({
        changes: { from, to: toCalc, insert: text },
      });
    };

    const actionNewDoc = ({ text }) => {
      const currentText = view.current.state.doc.toString();
      const currentPos = view.current.state.selection.ranges[0].from;
      const to = currentText.length;

      view.current.dispatch({
        changes: { from: 0, to, insert: text },
        selection: EditorSelection.cursor(currentPos),
      });
    };

    // eslint-disable-next-line no-param-reassign
    editorRef.current = {
      actionReplace,
      actionNewDoc,
    };

    const handleErrors = () => {
      view.current.dispatch({
        effects: filterMarks.of(() => false),
      });

      if (!error?.position) {
        return;
      }

      const textLength = view.current.state.doc.length;
      const fromPosition =
        error?.position + 1 <= textLength - 1 ? error.position : textLength - 1;
      const toPosition = fromPosition + 1;

      view.current.dispatch({
        effects: addMarks.of([errorMark.range(fromPosition, toPosition)]),
      });
    };

    const handleChange = (viewUpdate) => {
      const newValue = viewUpdate.state.doc.toString();
      const selection = viewUpdate.state?.selection?.ranges[0] || {};
      const { from, to } = selection;
      const selected = newValue.slice(from, to);
      const underCursor = from === to ? getCurrentWord(newValue, from) : {};

      if (selected !== currentSelection.current) {
        currentSelection.current = selected;
        onSelect({ selected, from, to });
      }

      if (underCursor.word !== currentUnderCursorWord.current) {
        currentUnderCursorWord.current = underCursor.word;
        onSetCursor(underCursor);
      }

      if (newValue !== currentValue.current) {
        currentValue.current = newValue;
        handleErrors();
        onChange(newValue);
      }
    };

    const errorHover = hoverTooltip((view, pos, side) => {
      // const { from, to, text } = view.state.doc.lineAt(pos);
      const hasErrors = view.state.field(markFieldExtension)?.size;
      if (!hasErrors) {
        return null;
      }
      return {
        pos,
        above: true,
        create(view) {
          const dom = document.createElement('div');
          dom.style = 'width: 100px; height: 100px';
          dom.textContent = 'error';
          return { dom };
        },
      };
    });

    const initEditor = () => {
      const extensions = [
        myTheme,
        basicSetup,
        StreamLanguage.define(yaml),
        EditorView.updateListener.of(handleChange),
        handleTabs && keymap.of([indentWithTab]),
        markFieldExtension,
        errorHover,
        errorStripe(getErrorPos),
        zebraStripes(),
        theme,
      ].filter(Boolean);

      const state = EditorState.create({
        doc: value,
        extensions,
      });
      view.current = new EditorView({ state, parent: mount?.current });
      window.view = view.current;
      window.actionReplace = actionReplace;
    };

    React.useEffect(() => {
      if (!mount.current) {
        throw new Error(`Can't find a mounting point for YamlEditor`);
      }
      initEditor();

      return () => {
        view.current.destroy();
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [theme]);

    React.useEffect(handleErrors);

    return <div ref={mount} />;
  },
);

export default YamlInput;
