pyinstaller movy_organizer.spec -y
cp -r "scripts" "dist/movy_organizer"
cp "settings.yaml" "dist/movy_organizer"
cp "icon.png" "dist/movy_organizer"
cp -r "pt_core_news_sm" "dist/movy_organizer"
cp -r "pt_core_news_sm-3.4.0.dist-info" "dist/movy_organizer"
