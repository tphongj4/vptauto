// Local test movie for native Flash input. No game URLs or network access.
import flash.display.Sprite;
import flash.display.GradientType;
import flash.display.StageAlign;
import flash.display.StageScaleMode;
import flash.events.MouseEvent;
import flash.events.TimerEvent;
import flash.geom.Matrix;
import flash.text.TextField;
import flash.text.TextFormat;
import flash.utils.Timer;

class Main extends Sprite {
    var pane:Sprite;
    var selected:Int = 1;
    var channel:Int = 0;
    var forceClicks:Int = 0;
    var confirmations:Int = 0;
    var blocked:Bool = false;
    var badInput:Bool = false;

    public static function main() {
        flash.Lib.current.addChild(new Main());
    }

    public function new() {
        super();
        flash.Lib.current.stage.scaleMode = StageScaleMode.NO_SCALE;
        flash.Lib.current.stage.align = StageAlign.TOP_LEFT;
        pane = new Sprite();
        pane.scaleX = pane.scaleY = .65;
        addChild(pane);
        login();
    }

    function clear() {
        while (pane.numChildren > 0) pane.removeChildAt(0);
        pane.graphics.clear();
        pane.graphics.beginFill(0x101010);
        pane.graphics.drawRect(0, 0, 1310, 850);
        pane.graphics.endFill();
    }

    function control(x:Float, y:Float, w:Float, h:Float, name:String, action:Void->Void, color:Int = -1) {
        var s = new Sprite();
        s.x = x;
        s.y = y;
        s.buttonMode = true;
        s.graphics.lineStyle(3, 0x06515c);
        if (color < 0) {
            var m = new Matrix();
            m.createGradientBox(w, h, Math.PI / 2);
            s.graphics.beginGradientFill(GradientType.LINEAR,
                [0x28475b, 0x46697c, 0x00e8ce, 0x00d8c2, 0x075b68],
                [1, 1, 1, 1, 1], [0, 128, 178, 217, 255], m);
        } else s.graphics.beginFill(color);
        s.graphics.drawRoundRect(0, 0, w, h, 8);
        s.graphics.endFill();
        var t = new TextField();
        t.mouseEnabled = false;
        t.width = w;
        t.height = h;
        t.defaultTextFormat = new TextFormat("Arial", 14, 0xffeb61, true);
        t.text = name;
        s.addChild(t);
        s.addEventListener(MouseEvent.CLICK, function(_) action());
        pane.addChild(s);
    }

    function login() {
        clear();
        control(586, 622, 146, 28, "Start", function() {});
        control(612, 675, 96, 24, "Force", forceLogin);
    }

    function forceLogin() {
        forceClicks++;
        if (blocked) {
            badInput = true;
            return;
        }
        blocked = true;
        // Keep the original buttons visible behind an eight-second progress
        // dialog. Only a confirmed notice allows another Force attempt.
        var dialog = new Sprite();
        dialog.x = 470;
        dialog.y = 350;
        dialog.graphics.lineStyle(3, 0x32c4d8);
        dialog.graphics.beginFill(0x155b68);
        dialog.graphics.drawRoundRect(0, 0, 370, 146, 8);
        dialog.graphics.endFill();
        var text = new TextField();
        text.x = 15;
        text.y = 40;
        text.width = 340;
        text.defaultTextFormat = new TextFormat("Arial", 16, 0xffffff);
        text.text = "Waiting for the old session...";
        dialog.addChild(text);
        pane.addChild(dialog);
        var bar = new Sprite();
        dialog.addChild(bar);
        var timer = new Timer(100, 80);
        timer.addEventListener(TimerEvent.TIMER, function(_) {
            bar.graphics.clear();
            bar.graphics.beginFill(0xeeeeee);
            bar.graphics.drawRect(55, 97, 260, 10);
            bar.graphics.endFill();
            bar.graphics.beginFill(0x32b6f1);
            bar.graphics.drawRect(55, 97, 260 * timer.currentCount / 80, 10);
            bar.graphics.endFill();
        });
        timer.addEventListener(TimerEvent.TIMER_COMPLETE, function(_) {
            if (forceClicks == 1) loginNotice();
            else channels();
        });
        timer.start();
    }

    function loginNotice() {
        login();
        pane.graphics.lineStyle(3, 0x32c4d8);
        pane.graphics.beginFill(0x002d2d);
        pane.graphics.drawRoundRect(480, 400, 352, 80, 8);
        pane.graphics.endFill();
        var text = new TextField();
        text.x = 495;
        text.y = 409;
        text.width = 325;
        text.defaultTextFormat = new TextFormat("Arial", 14, 0xffffff);
        text.text = "Link expired, please log in again";
        pane.addChild(text);
        control(618, 442, 78, 24, "OK", function() {
            confirmations++;
            blocked = false;
            login();
        });
    }

    function channels() {
        clear();
        for (i in 0...8) {
            var index = i;
            control(550, 287 + i * 42.5, 214, 28, 'Channel ${i + 1}', function() {
                channel = index + 1;
                characters();
            }, i == 1 ? 0xeeb332 : i == 7 ? 0x3ac587 : -1);
        }
    }

    function characters() {
        clear();
        for (i in 0...3) {
            var index = i;
            control(410 + i * 174, 548, 164, 76, 'Slot ${i + 1}', function() {
                selected = index + 1;
            }, 0x00cbd7);
        }
        control(442, 674, 102, 28, "Enter", function() {
            clear();
            var valid = forceClicks == 2 && confirmations == 1 && !badInput;
            pane.graphics.beginFill(valid ? 0x12ef00 + selected * 0x31 : 0xff00ff);
            pane.graphics.drawRect(0, 0, 1310, 850);
            pane.graphics.endFill();
        });
        control(818, 674, 70, 28, "Back", login);
        control(804, 471, 128, 28, "Reset", function() {});
    }
}
