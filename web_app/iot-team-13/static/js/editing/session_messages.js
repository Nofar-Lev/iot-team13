// Shared by the desktop editor and the phone editor: what each message of "one editor at a
// time" says, and what each of its buttons does. The wording is the same in both editors, so
// it is written once, here. How a message looks is each editor's own business (dialog.js
// builds the elements; each editor styles them).
//
// A message is a plain description, with no page elements:
//
//   {
//     name:      a short name, for the page's styles and the tests
//     title, text
//     countdown: null, or { seconds, warnsAsItRunsOut, label(secondsLeft) }
//     stacked:   true when the buttons are long and go one under the other
//     buttons:   [{ name, label, explanation, look, onClick }]
//                look is "main" (purple), "soft" (pale purple), "discards" (maroon) or "plain"
//     dismiss:   null, or { label, onClick }: a quiet way out that changes nothing. The
//                dialog offers it as a line under the buttons, as an X, and as a click
//                beside the dialog.
//   }

// The old editor's timer changes colour as it runs out: at these parts of the time left.
const TIME_LEFT_THAT_IS_SOON = 0.5;
const TIME_LEFT_THAT_IS_NOW = 0.25;

/**
 * How urgent a countdown is, from the part of its time that is left (1 at the start, 0 at
 * the end): "calm", then "soon", then "now".
 */
export function countdownStage(partOfTimeLeft) {
  if (partOfTimeLeft <= TIME_LEFT_THAT_IS_NOW) return "now";
  if (partOfTimeLeft <= TIME_LEFT_THAT_IS_SOON) return "soon";
  return "calm";
}

const seconds = (count) => (count === 1 ? "1 second" : `${count} seconds`);

const WHAT_BECAME_OF_THE_CHANGES = {
  carried_over: "Your unsaved changes were carried over to it.",
  discarded: "Your unsaved changes were discarded.",
  none: "You had no unsaved changes.",
};

/**
 * The message for a situation of the editing session (the names are in editing_session.js),
 * or null when the situation needs none: the editor is simply in use.
 *
 * session:   the editing session, for the answers.
 * goHome():  leave the editor for the home page.
 * reload():  load the editor again.
 */
export function messageFor(situation, { session, goHome, reload }) {
  const returnToHome = (look) => ({ name: "return-to-home", label: "Return to home", look, onClick: goHome });

  switch (situation.name) {
    case "draft_left_behind":
      return {
        name: "draft-left-behind",
        title: "Unsaved changes were left here",
        text: "The layout was being edited, and the changes were never saved. What should happen to them?",
        buttons: [
          { name: "resume", label: "Resume", look: "main", onClick: () => session.resumeDraftLeftBehind() },
          { name: "discard", label: "Discard", look: "discards", onClick: () => session.discardDraftLeftBehind() },
          returnToHome("plain"),
        ],
      };

    case "another_editor_has_unsaved_changes":
      return {
        name: "another-editor-has-unsaved-changes",
        title: "Another editor has unsaved changes",
        text: "The editor is open somewhere else, in the middle of changes. You can take over from it. It will be asked first.",
        stacked: true,
        buttons: [
          {
            name: "take-over-and-continue",
            label: "Take over and continue its changes",
            look: "main",
            onClick: () => session.askToTakeOver({ keepChanges: true }),
          },
          {
            name: "take-over-and-discard",
            label: "Take over and discard its changes",
            look: "discards",
            onClick: () => session.askToTakeOver({ keepChanges: false }),
          },
          returnToHome("plain"),
        ],
      };

    case "waiting_for_the_other_editor":
      return {
        name: "waiting-for-the-other-editor",
        title: "Waiting for the other editor",
        text: "It was asked to hand over. If it does not answer in time, you take over.",
        countdown: {
          seconds: situation.seconds,
          warnsAsItRunsOut: false,   // for this editor, the time running out is good news
          label: (secondsLeft) => `${seconds(secondsLeft)} left`,
        },
        buttons: [returnToHome("plain")],
      };

    case "take_over_refused":
      return {
        name: "take-over-refused",
        title: "The other editor is still in use",
        text: "It chose to go on editing. Try again later.",
        buttons: [returnToHome("main")],
      };

    case "take_over_in_progress":
      return {
        name: "take-over-in-progress",
        title: "Someone else is taking over the editor",
        text: "Try again in a moment.",
        buttons: [returnToHome("main")],
      };

    case "asked_to_hand_over":
      return {
        name: "asked-to-hand-over",
        title: "Another editor wants to take over",
        text: situation.keepChanges
          ? "It will continue from your unsaved changes. Nothing is lost."
          : "Your unsaved changes will be discarded.",
        countdown: {
          seconds: situation.seconds,
          warnsAsItRunsOut: true,
          label: (secondsLeft) => `If you do not answer, it takes over in ${seconds(secondsLeft)}`,
        },
        buttons: [
          {
            name: "approve",
            label: "Approve",
            // Approving throws work away only when the other editor chose to discard it.
            look: situation.keepChanges ? "main" : "discards",
            onClick: () => session.approveTakeOver(),
          },
          { name: "refuse", label: "Refuse", look: "plain", onClick: () => session.refuseTakeOver() },
        ],
      };

    case "taken_over":
      return {
        name: "taken-over",
        title: "Another editor is now in use",
        text: WHAT_BECAME_OF_THE_CHANGES[situation.changes],
        buttons: [returnToHome("main")],
      };

    case "connection_lost":
      return {
        name: "connection-lost",
        title: "The connection was lost",
        text: "The editor cannot be used without a connection to the server. Everything up to your last change is kept.",
        buttons: [{ name: "reload", label: "Reload", look: "main", onClick: reload }],
      };

    default:
      return null;   // "editing" and "back_to_editing": no message, the editor is in use
  }
}

/**
 * The question asked when the user leaves the editor with unsaved changes: three ways to
 * leave, each with a line that says what happens, and a quiet way to stay.
 */
export function leavingQuestion({ keepAsDraft, saveChanges, discardChanges, returnToTheEditor }) {
  return {
    name: "leaving-with-unsaved-changes",
    title: "You have unsaved changes",
    stacked: true,
    buttons: [
      {
        name: "keep-as-draft",
        label: "Keep as draft",
        explanation: "Finish later. The display stays as it is.",
        look: "main",
        onClick: keepAsDraft,
      },
      {
        name: "save-changes",
        label: "Save changes",
        explanation: "The display shows them now.",
        look: "soft",
        onClick: saveChanges,
      },
      {
        name: "discard-changes",
        label: "Discard changes",
        explanation: "Your changes are erased.",
        look: "discards",
        onClick: discardChanges,
      },
    ],
    dismiss: { label: "Return to the editor", onClick: returnToTheEditor },
  };
}
